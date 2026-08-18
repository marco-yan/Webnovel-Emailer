from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .mailer import send_gmail
from .scraper import Chapter, discover_chapters, extract_full_text


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"delivered": [], "last_run_utc": None}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def normalize_recipients(delivery: dict) -> list[str]:
    raw = delivery.get("recipients", delivery.get("recipient", []))
    if isinstance(raw, str):
        values = re.split(r"[,;\n]+", raw)
    else:
        values = [str(value) for value in (raw or [])]

    recipients: list[str] = []
    seen: set[str] = set()
    for value in values:
        email = value.strip()
        key = email.lower()
        if email and key not in seen:
            seen.add(key)
            recipients.append(email)

    if not recipients:
        raise RuntimeError("At least one recipient email must be configured")
    return recipients


def render_batch(chapters: list[Chapter], mode: str, include_source_link: bool) -> str:
    chunks: list[str] = []
    for chapter in chapters:
        chunks.append(chapter.title)
        chunks.append("=" * len(chapter.title))
        if mode == "full_text":
            chunks.append(chapter.body or "")
        else:
            chunks.append("Open this chapter at the source:")
        if include_source_link or mode == "links_only":
            chunks.append(chapter.url)
        chunks.append("")
    return "\n".join(chunks).strip() + "\n"


def run(config_path: str, dry_run: bool = False) -> int:
    config = load_yaml(config_path)
    source = config["source"]
    delivery = config["delivery"]
    recipients = normalize_recipients(delivery)
    state_path = Path(config.get("state", {}).get("path", "data/state.json"))

    mode = delivery.get("delivery_mode", "links_only")
    rights_confirmed = bool(delivery.get("rights_confirmed", False))
    if mode not in {"links_only", "full_text"}:
        raise ValueError("delivery_mode must be links_only or full_text")
    if mode == "full_text" and not rights_confirmed:
        raise RuntimeError(
            "Full-text delivery is disabled until rights_confirmed is true. "
            "Use it only for public-domain, self-authored, or authorized material."
        )

    discovered = discover_chapters(source)
    state = load_state(state_path)
    delivered = set(state.get("delivered", []))
    pending = [chapter for chapter in discovered if chapter.url not in delivered]

    batch_size = max(1, int(delivery.get("chapters_per_email", 3)))
    batch = pending[:batch_size]
    if not batch:
        print("No undelivered chapters found.")
        return 0

    if mode == "full_text":
        batch = [extract_full_text(chapter, source) for chapter in batch]

    first = batch[0].title
    last = batch[-1].title
    prefix = delivery.get("subject_prefix", "Reading batch")
    subject = f"{prefix}: {first}" if len(batch) == 1 else f"{prefix}: {first} → {last}"
    body = render_batch(batch, mode, bool(delivery.get("include_source_link", True)))

    if dry_run:
        print(f"TO: {', '.join(recipients)}")
        print(f"SUBJECT: {subject}\n")
        print(body)
        return 0

    send_gmail(recipients, subject, body)
    state["delivered"] = list(dict.fromkeys(state.get("delivered", []) + [c.url for c in batch]))
    state["last_run_utc"] = datetime.now(timezone.utc).isoformat()
    save_state(state_path, state)
    print(f"Delivered {len(batch)} chapter(s) to {len(recipients)} recipient(s).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Deliver a low-noise reading batch by Gmail.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return run(args.config, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
