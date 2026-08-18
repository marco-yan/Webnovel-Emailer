from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler

from src.auth import require_access_key
from src.scraper import discover_novel


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
            url = str(payload.get("url", "")).strip()
            novel = discover_novel(url)
            self._json(
                200,
                {
                    "title": novel.title,
                    "source_url": novel.source_url,
                    "total_chapters": len(novel.chapters),
                },
            )
        except PermissionError as exc:
            self._json(401, {"error": str(exc), "code": "ACCESS_DENIED"})
        except RuntimeError as exc:
            self._json(503, {"error": str(exc), "code": "SERVER_NOT_CONFIGURED"})
        except Exception as exc:
            self._json(400, {"error": str(exc)})
