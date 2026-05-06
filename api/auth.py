import json
import os
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler


GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


class handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self._send(204, {})

    def do_POST(self) -> None:
        length = int(self.headers.get("content-length") or "0")
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}

        credential = str(data.get("credential") or "").strip()
        client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
        if not client_id:
            self._send(503, {"error": "GOOGLE_CLIENT_ID is not configured."})
            return
        if not credential:
            self._send(400, {"error": "Missing Google credential."})
            return

        query = urllib.parse.urlencode({"id_token": credential})
        try:
            request = urllib.request.Request(f"{GOOGLE_TOKENINFO_URL}?{query}")
            with urllib.request.urlopen(request, timeout=8) as response:
                profile = json.loads(response.read().decode("utf-8"))
        except Exception:
            self._send(401, {"error": "Google credential could not be verified."})
            return

        if profile.get("aud") != client_id:
            self._send(401, {"error": "Google credential audience does not match this Jarvis app."})
            return
        if str(profile.get("email_verified", "")).lower() not in {"true", "1"}:
            self._send(401, {"error": "Google email is not verified."})
            return

        self._send(
            200,
            {
                "user": {
                    "name": profile.get("name") or profile.get("email", "Jarvis User"),
                    "email": profile.get("email", ""),
                    "picture": profile.get("picture", ""),
                    "provider": "google",
                }
            },
        )
