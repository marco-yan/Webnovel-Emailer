from __future__ import annotations

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


def _assert_allowed(url: str, allowed_domain: str) -> None:
    host = (urlparse(url).hostname or "").lower()
    allowed = allowed_domain.lower().strip()
    if host != allowed and not host.endswith("." + allowed):
        raise ValueError(f"Refusing URL outside configured domain: {host}")


def _get(url: str, cfg: dict) -> requests.Response:
    _assert_allowed(url, cfg["allowed_domain"])
    headers = {"User-Agent": cfg.get("user_agent", "Webnovel-Emailer/1.0")}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response


def discover_chapters(cfg: dict) -> list[Chapter]:
    """Discover ordered chapter links from an index / table-of-contents page."""
    response = _get(cfg["index_url"], cfg)
    soup = BeautifulSoup(response.text, "html.parser")
    selector = cfg["chapter_link_selector"]

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
        chapters.append(Chapter(title=title, url=url))
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
    body = "\n\n".join(
        part.strip()
        for part in body_node.stripped_strings
        if part.strip()
    )
    return Chapter(title=title, url=chapter.url, body=body)
