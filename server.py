from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from typing import Any

from remediator import RemediationError, analyze, remediate


ROOT = Path(__file__).resolve().parent


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/":
            content = (ROOT / "static" / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == "/api/health":
            self._json(200, {"status": "UP", "service": "security-remediation-agent"})
        else:
            self._json(404, {"status": "error", "message": "Not found"})

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            report = Path(payload["reportPath"])
            repository = Path(payload["repositoryPath"])
            if self.path == "/api/analyze":
                scanner, plans = analyze(report, repository)
                repo = repository.resolve()
                result: dict[str, Any] = {
                    "status": "ready", "scanner": scanner,
                    "changes": [plan.public(repo) for plan in plans],
                }
            elif self.path == "/api/remediate":
                result = remediate(
                    report, repository,
                    skip_validation=bool(payload.get("skipValidation", False)),
                    push=bool(payload.get("push", False)),
                    create_pr=bool(payload.get("openPr", False)),
                    base=str(payload.get("base", "main")),
                )
            else:
                self._json(404, {"status": "error", "message": "Not found"})
                return
            self._json(200, result)
        except (KeyError, json.JSONDecodeError, RemediationError) as exc:
            self._json(400, {"status": "error", "message": str(exc)})
        except Exception as exc:  # Keep the local demo UI responsive.
            self._json(500, {"status": "error", "message": str(exc)})

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        content = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[dashboard] {format % args}")


def serve(host: str = "127.0.0.1", port: int = 8080) -> None:
    print(f"Dashboard: http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
