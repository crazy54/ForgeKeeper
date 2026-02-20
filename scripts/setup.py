#!/usr/bin/env python3
"""
ForgeKeeper Pre-Build Setup Wizard (Flow A)
Runs on the HOST before docker build. Collects config, writes .env,
assembles a custom Dockerfile from selected language modules, then
triggers docker compose up --build.
"""
import json
import os
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETUP_UI = ROOT / "setup-ui"
ENV_FILE = ROOT / ".env"
DOCKERFILE_OUT = ROOT / "Dockerfile.built"
DOCKERFILE_BASE = ROOT / "Dockerfile"
LANG_MODULES_DIR = ROOT / "dockerfiles"
PORT = 7001

SUPPORTED_LANGS = ["python", "node", "go", "rust", "java", "dotnet", "ruby", "php", "swift", "dart"]

MIME_TYPES = {
    ".html": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".json": "application/json",
}


def write_env(config: dict) -> None:
    lines = [
        f'FORGEKEEPER_USER_EMAIL={config.get("email", "dev@example.com")}',
        f'FORGEKEEPER_HANDLE={config.get("handle", "forgekeeper")}',
        f'FORGEKEEPER_WORKSPACE={config.get("workspace", "workspace")}',
        f'GIT_USER_NAME={config.get("git_name", "")}',
        f'GIT_USER_EMAIL={config.get("git_email", "")}',
        f'GITHUB_TOKEN={config.get("github_token", "")}',
        f'OPENAI_API_KEY={config.get("openai_key", "")}',
        f'ANTHROPIC_API_KEY={config.get("anthropic_key", "")}',
        f'AWS_DEFAULT_REGION={config.get("aws_region", "us-east-1")}',
        f'OLLAMA_MODELS={",".join(config.get("ollama_models", ["llama3"]))}',
    ]
    ENV_FILE.write_text("\n".join(lines) + "\n")
    print(f"[setup] Wrote {ENV_FILE}")


def assemble_dockerfile(selected_langs: list) -> None:
    """Append selected language module snippets after the base Dockerfile."""
    if not DOCKERFILE_BASE.exists():
        print(f"[setup] WARNING: {DOCKERFILE_BASE} not found, skipping Dockerfile assembly.")
        return

    base = DOCKERFILE_BASE.read_text()
    lines = base.splitlines()
    expose_line = next((l for l in lines if l.startswith("EXPOSE")), "EXPOSE 8080 7000 7681 11434 8085 4000")
    base_no_expose = "\n".join(l for l in lines if not l.startswith("EXPOSE"))

    lang_blocks = []
    for lang in selected_langs:
        module = LANG_MODULES_DIR / f"lang-{lang}.dockerfile"
        if module.exists():
            lang_blocks.append(f"\n# ── Language Module: {lang} ──────────────────────\n")
            lang_blocks.append(module.read_text())
        else:
            print(f"[setup] WARNING: module not found for {lang}, skipping.")

    assembled = base_no_expose + "\n" + "".join(lang_blocks) + f"\n{expose_line}\n"
    DOCKERFILE_OUT.write_text(assembled)
    print(f"[setup] Assembled Dockerfile.built with langs: {selected_langs or ['(none — base only)']}")


def run_build() -> subprocess.Popen:
    # Write override so compose uses Dockerfile.built
    compose_override = ROOT / "docker-compose.override.yml"
    compose_override.write_text(
        "services:\n  forgekeeper:\n    build:\n      dockerfile: Dockerfile.built\n"
    )
    cmd = ["docker", "compose", "-f", str(ROOT / "docker-compose.yml"), "up", "--build", "-d"]
    print(f"[setup] Running: {' '.join(cmd)}")
    return subprocess.Popen(
        cmd, cwd=str(ROOT), env={**os.environ},
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )


class SetupHandler(BaseHTTPRequestHandler):
    build_process = None
    build_log: list = []

    def log_message(self, fmt, *args):
        try:
            print(f"[setup] {self.address_string()} {fmt % args}")
        except Exception:
            pass

    def _send_response(self, status: int, content_type: str, body: bytes) -> None:
        """Send a complete HTTP response, swallowing all pipe/connection errors."""
        try:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
        except Exception:
            return
        try:
            self.wfile.write(body)
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    def _send_json(self, data: dict, status: int = 200) -> None:
        self._send_response(status, "application/json", json.dumps(data).encode())

    def _send_file(self, path: Path) -> None:
        try:
            if not path.exists():
                self.send_error(404, f"Not found: {path.name}")
                return
            content = path.read_bytes()
            mime = MIME_TYPES.get(path.suffix, "text/plain")
            self._send_response(200, mime, content)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        except Exception as exc:
            print(f"[setup] _send_file error ({path}): {exc}")

    def do_OPTIONS(self):
        try:
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    def do_GET(self):
        path = self.path.split("?")[0]
        try:
            if path in ("/", "/index.html"):
                self._send_file(SETUP_UI / "index.html")
            elif path == "/setup/langs":
                self._send_json({"langs": SUPPORTED_LANGS})
            elif path == "/setup/build-log":
                done = (
                    SetupHandler.build_process is not None
                    and SetupHandler.build_process.poll() is not None
                )
                self._send_json({"log": SetupHandler.build_log, "done": done})
            elif path.startswith("/logo/"):
                # Serve logo from repo root logo/ directory
                self._send_file(ROOT / path.lstrip("/"))
            else:
                # Serve any other static file from setup-ui/
                self._send_file(SETUP_UI / path.lstrip("/"))
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        except Exception as exc:
            print(f"[setup] GET error ({path}): {exc}")
            try:
                self.send_error(500, str(exc))
            except Exception:
                pass

    def _read_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(length) if length else b"{}"
            return json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            return {}

    def do_POST(self):
        payload = self._read_body()

        try:
            if self.path == "/setup/submit":
                selected_langs = payload.get("languages", [])
                write_env(payload)
                assemble_dockerfile(selected_langs)
                self._send_json({"status": "ok", "message": "Config saved. Ready to build."})

            elif self.path == "/setup/build":
                if SetupHandler.build_process and SetupHandler.build_process.poll() is None:
                    self._send_json({"status": "already_running"})
                    return
                SetupHandler.build_log = []

                def stream_build():
                    try:
                        proc = run_build()
                        SetupHandler.build_process = proc
                        for line in proc.stdout:
                            SetupHandler.build_log.append(line.rstrip())
                        proc.wait()
                        SetupHandler.build_log.append(
                            f"[setup] Build finished — exit code {proc.returncode}"
                        )
                    except Exception as exc:
                        SetupHandler.build_log.append(f"[setup] Build error: {exc}")

                threading.Thread(target=stream_build, daemon=True).start()
                self._send_json({"status": "started"})

            elif self.path == "/setup/stop":
                proc = SetupHandler.build_process
                if proc and proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    SetupHandler.build_log.append("[setup] Build process terminated by user.")
                    self._send_json({"status": "stopped"})
                else:
                    self._send_json({"status": "not_running"})

            elif self.path == "/setup/cleanup":
                # Remove dangling Docker images/containers/build cache created by this build
                try:
                    result = subprocess.run(
                        ["docker", "system", "prune", "-f", "--filter", "label=com.docker.compose.project=forgekeeper"],
                        capture_output=True, text=True, timeout=120,
                    )
                    # Also prune dangling images broadly (build cache)
                    subprocess.run(
                        ["docker", "image", "prune", "-f"],
                        capture_output=True, text=True, timeout=60,
                    )
                    freed = result.stdout.strip() or "Dangling build artifacts removed."
                    self._send_json({"status": "ok", "message": freed})
                except subprocess.TimeoutExpired:
                    self._send_json({"status": "timeout", "message": "Cleanup timed out — run: docker system prune -f"})
                except FileNotFoundError:
                    self._send_json({"status": "error", "message": "docker not found on PATH"}, 500)

            else:
                self._send_json({"error": "Not found"}, 404)

        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        except Exception as exc:
            print(f"[setup] POST error ({self.path}): {exc}")
            try:
                self._send_json({"error": str(exc)}, 500)
            except Exception:
                pass


def main():
    def open_browser():
        try:
            webbrowser.open(f"http://localhost:{PORT}")
        except Exception:
            pass  # gio / xdg-open not available — user opens manually

    print(f"""
╔══════════════════════════════════════════════╗
║   ForgeKeeper Setup Wizard                   ║
║   Open http://localhost:{PORT} in your browser ║
║   Press Ctrl+C to exit                       ║
╚══════════════════════════════════════════════╝
""")
    server = HTTPServer(("0.0.0.0", PORT), SetupHandler)
    threading.Timer(1.0, open_browser).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[setup] Wizard closed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
