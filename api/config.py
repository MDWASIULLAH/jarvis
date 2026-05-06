import json
import os
from http.server import BaseHTTPRequestHandler


def _env(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


class handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self._send(204, {})

    def do_GET(self) -> None:
        self._send(
            200,
            {
                "mode": "jarvis-cloud-agent",
                "google_client_id": os.getenv("GOOGLE_CLIENT_ID", "").strip(),
                "supabase_url": _env("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL", "VITE_SUPABASE_URL"),
                "supabase_anon_key": _env(
                    "SUPABASE_ANON_KEY",
                    "NEXT_PUBLIC_SUPABASE_ANON_KEY",
                    "SUPABASE_PUBLISHABLE_KEY",
                    "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
                    "VITE_SUPABASE_ANON_KEY",
                    "VITE_SUPABASE_PUBLISHABLE_KEY",
                ),
                "desktop_connector": "optional-local-core",
            },
        )
