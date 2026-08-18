from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler

from src.auth import require_access_key
from src.mailer import send_gmail_batches
from src.scraper import discover_novel
from src.web_service import build_plan, normalize_recipients, render_links_batch


class handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        try:
            require_access_key(self.headers.get("X-App-Key"))
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")

            source_url = str(payload.get("url", "")).strip()
            recipients = normalize_recipients(payload.get("recipients", ""))
            start = int(payload.get("start", 1))
            end = int(payload.get("end", 1))
            batch_size = int(payload.get("batch_size", 10))

            novel = discover_novel(source_url)
            plan = build_plan(novel, start, end, batch_size)

            total_messages = len(plan.batches) * len(recipients)
            if len(plan.batches) > 50 or total_messages > 100:
                raise ValueError(
                    "That selection would create too many emails at once. "
                    "Increase the chapters-per-email value or use a smaller range."
                )

            messages = [
                render_links_batch(novel, batch, index, len(plan.batches))
                for index, batch in enumerate(plan.batches, start=1)
            ]
            send_gmail_batches(recipients, messages)

            self._json(
                200,
                {
                    "ok": True,
                    "novel": novel.title,
                    "chapters": len(plan.chapters),
                    "emails_per_recipient": len(plan.batches),
                    "recipients": len(recipients),
                },
            )
        except PermissionError as exc:
            self._json(401, {"error": str(exc), "code": "ACCESS_DENIED"})
        except RuntimeError as exc:
            self._json(503, {"error": str(exc), "code": "SERVER_NOT_CONFIGURED"})
        except Exception as exc:
            self._json(400, {"error": str(exc)})
