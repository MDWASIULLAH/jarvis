import json
from http.server import BaseHTTPRequestHandler
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_agent import plan_task  # noqa: E402


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

        prompt = str(data.get("command") or data.get("prompt") or "").strip()
        if not prompt:
            self._send(400, {"type": "error", "message": "Missing prompt."})
            return

        plan = plan_task(prompt)
        if plan.get("approval_required"):
            self._send(
                200,
                {
                    "type": "confirm_action",
                    "action": "agent_workflow",
                    "message": "Jarvis web planner prepared an execution plan. Approve in the Local Core UI to run desktop actions.",
                    "plan": plan,
                },
            )
            return

        self._send(
            200,
            {
                "type": "answer",
                "message": "Jarvis can answer this directly. For live execution, keep the Local Core connector running.",
                "plan": plan,
            },
        )
