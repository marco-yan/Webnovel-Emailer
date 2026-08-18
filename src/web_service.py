from __future__ import annotations

import re
from dataclasses import dataclass

from .scraper import Chapter, Novel


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@dataclass(frozen=True)
class DeliveryPlan:
    chapters: list[Chapter]
    batches: list[list[Chapter]]
    start: int
    end: int
    batch_size: int


def normalize_recipients(raw: str | list[str]) -> list[str]:
    values = re.split(r"[,;\n]+", raw) if isinstance(raw, str) else list(raw)
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        email = str(value).strip()
        key = email.lower()
        if not email or key in seen:
            continue
        if not EMAIL_RE.match(email):
            raise ValueError(f"Invalid email address: {email}")
        seen.add(key)
        output.append(email)
    if not output:
        raise ValueError("Enter at least one recipient email")
    return output


def build_plan(novel: Novel, start: int, end: int, batch_size: int) -> DeliveryPlan:
    total = len(novel.chapters)
    if total < 1:
        raise ValueError("No chapters were detected")
    if start < 1 or end < 1 or start > end:
        raise ValueError("Choose a valid inclusive chapter range")
    if end > total:
        raise ValueError(f"This novel has {total} detected chapters")
    if batch_size < 1 or batch_size > 100:
        raise ValueError("Batch size must be between 1 and 100 chapters")

    selected = novel.chapters[start - 1 : end]
    batches = [selected[i : i + batch_size] for i in range(0, len(selected), batch_size)]
    return DeliveryPlan(selected, batches, start, end, batch_size)


def render_links_batch(novel: Novel, batch: list[Chapter], part: int, total_parts: int) -> tuple[str, str]:
    first = batch[0].number or 1
    last = batch[-1].number or first
    subject = f"{novel.title} - Chapters {first}-{last}"
    lines = [
        novel.title,
        f"Reading batch {part} of {total_parts}",
        f"Chapters {first}-{last}",
        "",
    ]
    for chapter in batch:
        label = chapter.title or f"Chapter {chapter.number or ''}".strip()
        lines.extend([label, chapter.url, ""])
    return subject, "\n".join(lines).strip() + "\n"
