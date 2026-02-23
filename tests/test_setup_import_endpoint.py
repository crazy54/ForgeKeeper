#!/usr/bin/env python3
"""
Unit tests for the POST /setup/import-devcontainer endpoint in setup.py.

Tests file upload handling, parser/mapper integration, and JSON response format.
"""
import json
import sys
from http.server import HTTPServer
from io import BytesIO
from pathlib import Path
from threading import Thread
from urllib.request import Request, urlopen
from urllib.error import URLError

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from setup import SetupHandler

PORT = 17123  # Use a high port unlikely to conflict


@pytest.fixture(scope="module")
def server():
    """Start a test HTTP server in a background thread."""
    srv = HTTPServer(("127.0.0.1", PORT), SetupHandler)
    t = Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield srv
    srv.shutdown()


def _build_multipart(file_content: bytes, field_name: str = "file", filename: str = "devcontainer.json"):
    """Build a multipart/form-data body with a single file field."""
    boundary = "----TestBoundary7MA4YWxkTrZu0gW"
    body = (
        f"------TestBoundary7MA4YWxkTrZu0gW\r\n"
        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
        f"Content-Type: application/json\r\n"
        f"\r\n"
    ).encode("utf-8") + file_content + (
        f"\r\n------TestBoundary7MA4YWxkTrZu0gW--\r\n"
    ).encode("utf-8")
    content_type = f"multipart/form-data; boundary=----TestBoundary7MA4YWxkTrZu0gW"
    return body, content_type


def _post(server, path, body, content_type):
    """Send a POST request and return parsed JSON response."""
    url = f"http://127.0.0.1:{PORT}{path}"
    req = Request(url, data=body, method="POST")
    req.add_header("Content-Type", content_type)
    with urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8")), resp.status


class TestImportDevcontainerEndpoint:
    """Tests for POST /setup/import-devcontainer."""

    def test_valid_devcontainer_with_features(self, server):
        """Upload a valid devcontainer.json with language features and verify mapping."""
        devcontainer = {
            "features": {
                "ghcr.io/devcontainers/features/python:1": {"version": "3.11"},
                "ghcr.io/devcontainers/features/node:1": {"version": "20"},
            },
            "forwardPorts": [3000, 8080],
            "remoteEnv": {"MY_VAR": "hello"},
        }
        body, ct = _build_multipart(json.dumps(devcontainer).encode("utf-8"))
        data, status = _post(server, "/setup/import-devcontainer", body, ct)

        assert status == 200
        assert data["success"] is True
        mapping = data["mapping"]
        assert "node" in mapping["languages"]
        assert "python" in mapping["languages"]
        assert mapping["languages"] == sorted(mapping["languages"])  # sorted
        assert mapping["ports"] == [3000, 8080]
        assert mapping["env_vars"] == {"MY_VAR": "hello"}
        assert mapping["unrecognized_features"] == []

    def test_valid_devcontainer_with_unrecognized_features(self, server):
        """Unrecognized features should appear in warnings."""
        devcontainer = {
            "features": {
                "ghcr.io/devcontainers/features/docker-in-docker:2": {},
            }
        }
        body, ct = _build_multipart(json.dumps(devcontainer).encode("utf-8"))
        data, _ = _post(server, "/setup/import-devcontainer", body, ct)

        assert data["success"] is True
        mapping = data["mapping"]
        assert mapping["languages"] == []
        assert len(mapping["unrecognized_features"]) == 1
        assert len(mapping["warnings"]) >= 1

    def test_valid_empty_devcontainer(self, server):
        """An empty object is valid — no features detected."""
        body, ct = _build_multipart(b"{}")
        data, _ = _post(server, "/setup/import-devcontainer", body, ct)

        assert data["success"] is True
        assert data["mapping"]["languages"] == []

    def test_invalid_json_returns_error(self, server):
        """Malformed JSON should return success=False with errors."""
        body, ct = _build_multipart(b"{ not valid json !!!")
        # The server returns 400 for parse errors
        req = Request(
            f"http://127.0.0.1:{PORT}/setup/import-devcontainer",
            data=body,
            method="POST",
        )
        req.add_header("Content-Type", ct)
        try:
            with urlopen(req) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            # urllib raises on 4xx — read the error body
            data = json.loads(e.read().decode("utf-8"))

        assert data["success"] is False
        assert len(data["errors"]) > 0

    def test_non_multipart_request_returns_error(self, server):
        """A plain JSON POST should be rejected with 400."""
        req = Request(
            f"http://127.0.0.1:{PORT}/setup/import-devcontainer",
            data=b'{"foo": "bar"}',
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        try:
            with urlopen(req) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            data = json.loads(e.read().decode("utf-8"))

        assert data["success"] is False
        assert "multipart" in data["errors"][0].lower()

    def test_image_based_language_detection(self, server):
        """Languages detected from image name should appear in result."""
        devcontainer = {
            "image": "mcr.microsoft.com/devcontainers/python:3.11",
        }
        body, ct = _build_multipart(json.dumps(devcontainer).encode("utf-8"))
        data, _ = _post(server, "/setup/import-devcontainer", body, ct)

        assert data["success"] is True
        assert "python" in data["mapping"]["languages"]


# Project root — must match ROOT in setup.py so temp files pass path validation
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _post_path_import(path_value):
    """Send a POST to /setup/import-devcontainer-path and return (parsed_json, status_code)."""
    body = json.dumps({"path": path_value}).encode("utf-8")
    req = Request(
        f"http://127.0.0.1:{PORT}/setup/import-devcontainer-path",
        data=body,
        method="POST",
    )
    req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8")), resp.status
    except Exception as e:
        return json.loads(e.read().decode("utf-8")), e.code


class TestImportDevcontainerPathEndpoint:
    """Tests for POST /setup/import-devcontainer-path."""

    def test_path_import_valid_devcontainer(self, server):
        """Path import with a valid devcontainer.json should return success with mapping."""
        devcontainer = {
            "features": {
                "ghcr.io/devcontainers/features/python:1": {"version": "3.11"},
                "ghcr.io/devcontainers/features/go:1": {},
            },
            "forwardPorts": [8080],
            "remoteEnv": {"APP_ENV": "dev"},
        }
        # Create temp file inside project root so it passes path validation
        tmp_file = _PROJECT_ROOT / "tests" / "_tmp_valid_devcontainer.json"
        try:
            tmp_file.write_text(json.dumps(devcontainer))
            data, status = _post_path_import(str(tmp_file))

            assert status == 200
            assert data["success"] is True
            mapping = data["mapping"]
            assert "python" in mapping["languages"]
            assert "go" in mapping["languages"]
            assert mapping["ports"] == [8080]
            assert mapping["env_vars"] == {"APP_ENV": "dev"}
            assert mapping["unrecognized_features"] == []
        finally:
            tmp_file.unlink(missing_ok=True)

    def test_path_import_missing_file(self, server):
        """Path import with a non-existent file inside project root should return file-not-found error."""
        missing = str(_PROJECT_ROOT / "tests" / "_nonexistent_devcontainer.json")
        data, status = _post_path_import(missing)

        assert data["success"] is False
        assert status == 404
        assert any("not found" in err.lower() for err in data["errors"])

    def test_path_import_invalid_json(self, server):
        """Path import with a file containing invalid JSON should return a parse error."""
        tmp_file = _PROJECT_ROOT / "tests" / "_tmp_bad_devcontainer.json"
        try:
            tmp_file.write_text("{ this is not valid json !!!")
            data, status = _post_path_import(str(tmp_file))

            assert data["success"] is False
            assert len(data["errors"]) > 0
        finally:
            tmp_file.unlink(missing_ok=True)

    def test_path_import_path_traversal(self, server):
        """Path import with a path outside the project root should be rejected."""
        data, status = _post_path_import("/etc/passwd")

        assert data["success"] is False
        assert any("traversal" in err.lower() or "invalid path" in err.lower() for err in data["errors"])

    def test_path_import_no_path_provided(self, server):
        """Request with no 'path' field should return an error."""
        body = json.dumps({}).encode("utf-8")
        req = Request(
            f"http://127.0.0.1:{PORT}/setup/import-devcontainer-path",
            data=body,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        try:
            with urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            data = json.loads(e.read().decode("utf-8"))

        assert data["success"] is False
        assert any("no path" in err.lower() for err in data["errors"])

    def test_path_import_empty_path(self, server):
        """Request with an empty string path should return an error."""
        data, status = _post_path_import("")

        assert data["success"] is False
        assert any("no path" in err.lower() for err in data["errors"])
