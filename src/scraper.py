from __future__ import annotations

import ipaddress
import re
import socket
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class Chapter:
    title: str
    url: str
    body: str | None = None
    number: int | None = None


@dataclass(frozen=True)
class Novel:
    title: str
    source_url: str
    chapters: list[Chapter]


def _assert_allowed(url: str, allowed_domain: str) -> None:
    host = (urlparse(url).hostname or "").lower()
    allowed = allowed_domain.lower().strip()
    if host != allowed and not host.endswith("." + allowed):
        raise ValueError(f"Refusing URL outside configured domain: {host}")


def _assert_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only public http(s) URLs are supported")

    host = parsed.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
        raise ValueError("Local network addresses are not supported")

    try:
        direct_ip = ipaddress.ip_address(host)
    except ValueError:
        direct_ip = None

    if direct_ip is not None:
        if not direct_ip.is_global:
            raise ValueError("Private or reserved network addresses are not supported")
        return

    try:
        addresses = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ValueError("Could not resolve the source website") from exc

    if not addresses:
        raise ValueError("Could not resolve the source website")

    for entry in addresses:
        address = entry[4][0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            continue
        if not ip.is_global:
            raise ValueError("Private or reserved network addresses are not supported")


def _get(url: str, cfg: dict) -> requests.Response:
    headers = {"User-Agent": cfg.get("user_agent", "Webnovel-Emailer/2.0")}
    current = url

    for _ in range(4):
        _assert_allowed(current, cfg["allowed_domain"])
        _assert_public_url(current)
        response = requests.get(
            current,
            headers=headers,
            timeout=30,
            allow_redirects=False,
        )

        if response.status_code in {301, 302, 303, 307, 308}:
            location = response.headers.get("Location")
            if not location:
                response.raise_for_status()
            current = urljoin(current, location)
            continue

        response.raise_for_status()
        return response

    raise ValueError("Too many redirects while opening the source website")


def _chapter_number(text: str, href: str) -> int | None:
    candidates = [text, href]
    patterns = [
        r"(?:chapter|chap|ch)\s*[-:#.]?\s*(\d{1,6})\b",
        r"/chapter/(\d{1,6})(?:/|$)",
        r"chapter[-_/](\d{1,6})(?:\D|$)",
    ]
    for value in candidates:
        lowered = value.lower()
        for pattern in patterns:
            match = re.search(pattern, lowered)
            if match:
                return int(match.group(1))
    return None


def _page_title(soup: BeautifulSoup, fallback: str) -> str:
    for selector in ["h1", "meta[property='og:title']", "title"]:
        node = soup.select_one(selector)
        if not node:
            continue
        if node.name == "meta":
            value = (node.get("content") or "").strip()
        else:
            value = node.get_text(" ", strip=True)
        if value:
            return re.sub(r"\s+-\s+.*$", "", value).strip()
    return fallback


def _lightnovelworld_chapters(index_url: str, soup: BeautifulSoup) -> list[Chapter]:
    text = soup.get_text(" ", strip=True)
    matches = [int(value) for value in re.findall(r"\b(\d{1,6})\s+Chapters\b", text, flags=re.I)]
    if not matches:
        return []

    total = max(matches)
    base = index_url.rstrip("/") + "/"

    # LightNovelWorld exposes stable numbered chapter routes. The public app
    # organizes source links; it does not reproduce third-party chapter prose.
    by_number: dict[int, Chapter] = {
        number: Chapter(
            title=f"Chapter {number}",
            url=urljoin(base, f"chapter/{number}/"),
            number=number,
        )
        for number in range(1, total + 1)
    }

    # Keep any chapter titles that are already present on the novel page.
    for node in soup.select("a[href]"):
        href = node.get("href") or ""
        label = node.get_text(" ", strip=True)
        number = _chapter_number(label, href)
        if number is None or number not in by_number:
            continue
        if label and "chapter" in (label + " " + href).lower():
            by_number[number] = Chapter(
                title=label,
                url=urljoin(index_url, href),
                number=number,
            )

    return [by_number[number] for number in sorted(by_number)]


def _generic_chapters(index_url: str, soup: BeautifulSoup, allowed_domain: str) -> list[Chapter]:
    by_number: dict[int, Chapter] = {}
    for node in soup.select("a[href]"):
        href = node.get("href") or ""
        label = node.get_text(" ", strip=True)
        combined = f"{label} {href}".lower()
        if "chapter" not in combined and not re.search(r"(?:^|[\W_])ch(?:apter)?[\W_]*\d", combined):
            continue
        number = _chapter_number(label, href)
        if number is None:
            continue
        url = urljoin(index_url, href)
        try:
            _assert_allowed(url, allowed_domain)
        except ValueError:
            continue
        if number not in by_number:
            by_number[number] = Chapter(
                title=label or f"Chapter {number}",
                url=url,
                number=number,
            )
    return [by_number[number] for number in sorted(by_number)]


def discover_novel(index_url: str) -> Novel:
    """Automatically identify a novel title and its numbered chapter links."""
    parsed = urlparse(index_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Enter a valid http(s) novel URL")

    _assert_public_url(index_url)
    allowed_domain = parsed.hostname.lower()
    cfg = {
        "allowed_domain": allowed_domain,
        "user_agent": "Webnovel-Emailer/2.0 (+chapter-link organizer)",
    }
    response = _get(index_url, cfg)
    soup = BeautifulSoup(response.text, "html.parser")
    title = _page_title(soup, allowed_domain)

    if allowed_domain == "lightnovelworld.org" or allowed_domain.endswith(".lightnovelworld.org"):
        chapters = _lightnovelworld_chapters(index_url, soup)
    else:
        chapters = _generic_chapters(index_url, soup, allowed_domain)

    if not chapters:
        raise ValueError(
            "I could not detect numbered chapter links on that page automatically yet. "
            "This source may need a small site adapter."
        )
    return Novel(title=title, source_url=index_url, chapters=chapters)


def discover_chapters(cfg: dict) -> list[Chapter]:
    """Discover ordered chapter links; explicit selectors remain supported for CLI use."""
    selector = (cfg.get("chapter_link_selector") or "").strip()
    if not selector or selector.lower() == "auto":
        return discover_novel(cfg["index_url"]).chapters

    response = _get(cfg["index_url"], cfg)
    soup = BeautifulSoup(response.text, "html.parser")
    seen: set[str] = set()
    chapters: list[Chapter] = []
    for node in soup.select(selector):
        href = node.get("href")
        if not href:
            continue
        url = urljoin(cfg["index_url"], href)
        _assert_allowed(url, cfg["allowed_domain"])
        if url in seen:
            continue
        seen.add(url)
        title = node.get_text(" ", strip=True) or url
        chapters.append(Chapter(title=title, url=url, number=_chapter_number(title, href)))
    return chapters


def extract_full_text(chapter: Chapter, cfg: dict) -> Chapter:
    """Extract full text only after the caller has confirmed reproduction rights."""
    delay = float(cfg.get("request_delay_seconds", 2.0))
    if delay > 0:
        time.sleep(delay)

    response = _get(chapter.url, cfg)
    soup = BeautifulSoup(response.text, "html.parser")

    title_node = soup.select_one(cfg.get("chapter_title_selector", "h1"))
    body_node = soup.select_one(cfg["chapter_body_selector"])
    if body_node is None:
        raise ValueError(f"Chapter body selector did not match: {chapter.url}")

    for unwanted in body_node.select("script, style, noscript, iframe"):
        unwanted.decompose()

    title = title_node.get_text(" ", strip=True) if title_node else chapter.title
    body = "\n\n".join(part.strip() for part in body_node.stripped_strings if part.strip())
    return Chapter(title=title, url=chapter.url, body=body, number=chapter.number)
