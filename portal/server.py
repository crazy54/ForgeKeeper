#!/usr/bin/env python3
"""
ForgeKeeper Portal Server
Serves the portal UI and exposes control, setup, and runtime management endpoints.
"""
import json
import os
import subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# ROOT is always the portal/ directory, regardless of CWD
ROOT = Path(__file__).resolve().parent

# setup-ui is a sibling of portal/ inside the container at /opt/forgekeeper/
# Fall back to a relative path for local dev (running from repo root)
_SETUP_UI_CONTAINER = Path("/opt/forgekeeper/setup-ui")
_SETUP_UI_LOCAL = ROOT.parent / "setup-ui"
SETUP_UI = _SETUP_UI_CONTAINER if _SETUP_UI_CONTAINER.exists() else _SETUP_UI_LOCAL

# Runtime paths — always inside the container
CONTROL_SCRIPT = Path("/usr/local/bin/forgekeeper-control.sh")
RUNTIME_SCRIPT = Path("/usr/local/bin/forgekeeper-runtime")
SETUP_COMPLETE = Path("/etc/forgekeeper/.setup-complete")
ENV_FILE = Path("/etc/forgekeeper/env")
LOG_DIR = Path("/var/log/forgekeeper")
LOG_FILE = LOG_DIR / "portal-access.log"
LANG_STATE_DIR = Path("/etc/forgekeeper/langs")

ALLOWED_ACTIONS = {"shutdown", "reset"}
ALLOWED_LANGS = {"python", "node", "go", "rust", "java", "dotnet", "ruby", "php", "swift", "dart"}

MIME_TYPES = {
    ".html": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
}


def _log(message: str) -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(f"{message}\n")
    except OSError:
        pass


def _send_json(handler, data: dict, status: int = 200) -> None:
    """Send JSON response, swallowing broken-pipe errors."""
    body = json.dumps(data).encode()
    try:
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
    except (BrokenPipeError, ConnectionResetError, OSError):
        return
    try:
        handler.wfile.write(body)
        handler.wfile.flush()
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass


def _read_body(handler) -> dict:
    try:
        length = int(handler.headers.get("Content-Length", "0") or 0)
        raw = handler.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8")) if raw else {}
    except Exception:
        return {}


class ForgeKeeperHandler(SimpleHTTPRequestHandler):

    def translate_path(self, path):
        """Map URL paths to filesystem paths under ROOT (portal dir)."""
        path = path.split("?", 1)[0].split("#", 1)[0]
        if path in ("/", ""):
            path = "/index.html"
        return str(ROOT / path.lstrip("/"))

    def log_message(self, fmt, *args):
        msg = "%s - - [%s] %s" % (
            self.client_address[0],
            self.log_date_time_string(),
            fmt % args,
        )
        _log(msg)

    # ── GET ───────────────────────────────────────────────────────────────────
    def do_GET(self):
        path = self.path.split("?")[0]

        # Setup gate — redirect to wizard if first-run not complete (Flow B)
        if path == "/" and not SETUP_COMPLETE.exists():
            try:
                self.send_response(302)
                self.send_header("Location", "/setup")
                self.end_headers()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            return

        if path == "/setup":
            self._serve_file(SETUP_UI / "index.html")
            return

        if path.startswith("/setup-ui/"):
            self._serve_file(SETUP_UI / path[len("/setup-ui/"):])
            return

        if path.startswith("/logo/"):
            # Serve logo assets from the repo root logo/ directory
            _LOGO_DIR_CONTAINER = Path("/opt/forgekeeper/logo")
            _LOGO_DIR_LOCAL = ROOT.parent / "logo"
            logo_dir = _LOGO_DIR_CONTAINER if _LOGO_DIR_CONTAINER.exists() else _LOGO_DIR_LOCAL
            self._serve_file(logo_dir / path[len("/logo/"):])
            return

        if path == "/forgekeeper/runtime/list":
            self._handle_runtime_list()
            return

        # Default: serve portal static files
        super().do_GET()

    # ── POST ──────────────────────────────────────────────────────────────────
    def do_POST(self):
        path = self.path
        if path == "/forgekeeper/control":
            self._handle_control()
        elif path in ("/forgekeeper/setup", "/setup/submit"):
            self._handle_setup()
        elif path == "/forgekeeper/runtime":
            self._handle_runtime()
        else:
            self.send_error(404, "Not Found")

    # ── Handlers ──────────────────────────────────────────────────────────────
    def _handle_control(self) -> None:
        payload = _read_body(self)
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
                check=True, capture_output=True, text=True,
            )
            _send_json(self, {"status": "ok", "message": result.stdout.strip() or f"ForgeKeeper {action} accepted."})
        except subprocess.CalledProcessError as exc:
            self.send_error(500, f"Control failed: {exc.stderr or exc.stdout}")

    def _handle_setup(self) -> None:
        """Flow B: receive wizard config, write env file, mark setup complete."""
        payload = _read_body(self)
        try:
            ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
            lines = [
                f'FORGEKEEPER_HANDLE={payload.get("handle", "forgekeeper")}',
                f'FORGEKEEPER_USER_EMAIL={payload.get("email", "dev@example.com")}',
                f'FORGEKEEPER_WORKSPACE={payload.get("workspace", "workspace")}',
                f'GIT_USER_NAME={payload.get("git_name", "")}',
                f'GIT_USER_EMAIL={payload.get("git_email", "")}',
                f'GITHUB_TOKEN={payload.get("github_token", "")}',
                f'OPENAI_API_KEY={payload.get("openai_key", "")}',
                f'ANTHROPIC_API_KEY={payload.get("anthropic_key", "")}',
                f'AWS_DEFAULT_REGION={payload.get("aws_region", "us-east-1")}',
            ]
            ENV_FILE.write_text("\n".join(lines) + "\n")

            # Source env into new shell sessions
            profile_snippet = Path("/etc/profile.d/10-forgekeeper-env.sh")
            try:
                profile_snippet.write_text(f'set -a; source {ENV_FILE}; set +a\n')
            except OSError:
                pass  # non-fatal if /etc/profile.d isn't writable

            # Kick off language installs in background
            selected_langs = payload.get("languages", [])
            for lang in selected_langs:
                if lang in ALLOWED_LANGS and RUNTIME_SCRIPT.exists():
                    subprocess.Popen(["sudo", str(RUNTIME_SCRIPT), "install", lang])

            # Mark setup complete
            SETUP_COMPLETE.parent.mkdir(parents=True, exist_ok=True)
            SETUP_COMPLETE.touch()

            _send_json(self, {"status": "ok", "message": "Setup complete."})
        except Exception as exc:
            _log(f"Setup error: {exc}")
            self.send_error(500, str(exc))

    def _handle_runtime(self) -> None:
        """Install or remove a language runtime inside the running container."""
        payload = _read_body(self)
        action = payload.get("action")
        lang = payload.get("lang", "")

        if action not in ("install", "remove"):
            self.send_error(400, "action must be install or remove")
            return
        if lang not in ALLOWED_LANGS:
            self.send_error(400, f"Unknown language: {lang}")
            return
        if not RUNTIME_SCRIPT.exists():
            self.send_error(500, "Runtime script not found")
            return

        try:
            result = subprocess.run(
                ["sudo", str(RUNTIME_SCRIPT), action, lang],
                check=True, capture_output=True, text=True, timeout=600,
            )
            _send_json(self, {"status": "ok", "message": result.stdout.strip()})
        except subprocess.TimeoutExpired:
            _send_json(self, {"status": "timeout", "message": f"{lang} {action} timed out after 10 min."}, 202)
        except subprocess.CalledProcessError as exc:
            self.send_error(500, f"Runtime {action} failed: {exc.stderr or exc.stdout}")

    def _handle_runtime_list(self) -> None:
        """Return installed/available language status."""
        langs = []
        for lang in sorted(ALLOWED_LANGS):
            langs.append({
                "id": lang,
                "installed": (LANG_STATE_DIR / f"{lang}.installed").exists(),
            })
        _send_json(self, {"langs": langs})

    def _serve_file(self, path: Path) -> None:
        """Serve a file with proper MIME type and pipe-safe response."""
        try:
            if not path.exists():
                self.send_error(404, f"Not found: {path.name}")
                return
            content = path.read_bytes()
            mime = MIME_TYPES.get(path.suffix, "text/plain")
            try:
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
            except (BrokenPipeError, ConnectionResetError, OSError):
                return
            try:
                self.wfile.write(content)
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
        except Exception as exc:
            _log(f"_serve_file error ({path}): {exc}")


if __name__ == "__main__":
    port = int(os.environ.get("FORGEKEEPER_PORTAL_PORT", "7000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), ForgeKeeperHandler)
    print(f"[portal] Listening on :{port}  (ROOT={ROOT}, SETUP_UI={SETUP_UI})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
