#!/usr/bin/env python3
import json
import os
import subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALLOWED_ACTIONS = {"shutdown", "reset"}
CONTROL_SCRIPT = Path("/usr/local/bin/forgekeeper-control.sh")
LOG_FILE = Path("/var/log/forgekeeper/portal-access.log")


def log_message(message: str) -> None:
  LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
  with LOG_FILE.open("a", encoding="utf-8") as handle:
    handle.write(f"{message}\n")


class ForgeKeeperHandler(SimpleHTTPRequestHandler):
  def translate_path(self, path):
    path = path.split("?", 1)[0].split("#", 1)[0]
    if path == "/" or path == "":
      path = "/index.html"
    target = ROOT / path.lstrip("/")
    return str(target)

  def log_message(self, format, *args):  # noqa: A003 - override
    message = "%s - - [%s] %s\n" % (self.client_address[0], self.log_date_time_string(), format % args)
    log_message(message.rstrip())

  def do_POST(self):  # noqa: N802 (legacy signature)
    if self.path != "/forgekeeper/control":
      self.send_error(404, "Not Found")
      return

    content_length = int(self.headers.get("Content-Length", "0") or 0)
    raw_body = self.rfile.read(content_length) if content_length else b"{}"
    try:
      payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except json.JSONDecodeError:
      self.send_error(400, "Invalid JSON")
      return

    action = payload.get("action")
    if action not in ALLOWED_ACTIONS:
      self.send_error(400, "Unknown action")
      return

    if not CONTROL_SCRIPT.exists():
      self.send_error(500, "Control script missing")
      return

    try:
      result = subprocess.run(
        ["sudo", str(CONTROL_SCRIPT), action],
        check=True,
        capture_output=True,
        text=True,
      )
      message = result.stdout.strip() or f"ForgeKeeper {action} accepted."
      self.send_response(200)
      self.send_header("Content-Type", "application/json")
      self.end_headers()
      self.wfile.write(json.dumps({"status": "ok", "message": message}).encode("utf-8"))
    except subprocess.CalledProcessError as exc:
      self.send_error(500, f"Control failed: {exc.stderr or exc.stdout}")


if __name__ == "__main__":
  port = int(os.environ.get("FORGEKEEPER_PORTAL_PORT", "7000"))
  server = ThreadingHTTPServer(("0.0.0.0", port), ForgeKeeperHandler)
  print(f"ForgeKeeper portal listening on :{port}")
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    pass
