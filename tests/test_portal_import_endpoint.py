#!/usr/bin/env python3
"""
Unit tests for the POST /forgekeeper/import-devcontainer endpoint in portal/server.py.

Tests file upload handling, parser/mapper integration, and JSON response format
for the Flow B (portal) import endpoint.
"""
import json
import sys
from http.server import HTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import Request, urlopen

import pytest

# Add scripts directory to path so portal/server.py can import parser/mapper
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
# Add portal directory to path so we can import server module
sys.path.insert(0, str(Path(__file__).parent.parent / "portal"))

from server import ForgeKeeperHandler

PORT = 17124  # Different port from Flow A tests to avoid conflicts


@pytest.fixture(scope="module")
def server():
    """Start a test HTTP server in a background thread."""
    srv = HTTPServer(("127.0.0.1", PORT), ForgeKeeperHandler)
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


class TestPortalImportDevcontainerEndpoint:
    """Tests for POST /forgekeeper/import-devcontainer."""

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
        data, status = _post(server, "/forgekeeper/import-devcontainer", body, ct)

        assert status == 200
        assert data["success"] is True
        mapping = data["mapping"]
        assert "node" in mapping["languages"]
        assert "python" in mapping["languages"]
        assert mapping["languages"] == sorted(mapping["languages"])
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
        data, _ = _post(server, "/forgekeeper/import-devcontainer", body, ct)

        assert data["success"] is True
        mapping = data["mapping"]
        assert mapping["languages"] == []
        assert len(mapping["unrecognized_features"]) == 1
        assert len(mapping["warnings"]) >= 1

    def test_valid_empty_devcontainer(self, server):
        """An empty object is valid — no features detected."""
        body, ct = _build_multipart(b"{}")
        data, _ = _post(server, "/forgekeeper/import-devcontainer", body, ct)

        assert data["success"] is True
        assert data["mapping"]["languages"] == []

    def test_invalid_json_returns_error(self, server):
        """Malformed JSON should return success=False with errors."""
        body, ct = _build_multipart(b"{ not valid json !!!")
        req = Request(
            f"http://127.0.0.1:{PORT}/forgekeeper/import-devcontainer",
            data=body,
            method="POST",
        )
        req.add_header("Content-Type", ct)
        try:
            with urlopen(req) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            data = json.loads(e.read().decode("utf-8"))

        assert data["success"] is False
        assert len(data["errors"]) > 0

    def test_non_multipart_request_returns_error(self, server):
        """A plain JSON POST should be rejected with 400."""
        req = Request(
            f"http://127.0.0.1:{PORT}/forgekeeper/import-devcontainer",
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
        data, _ = _post(server, "/forgekeeper/import-devcontainer", body, ct)

        assert data["success"] is True
        assert "python" in data["mapping"]["languages"]


def _post_json(server, path, payload):
    """Send a JSON POST request and return parsed JSON response + status."""
    url = f"http://127.0.0.1:{PORT}{path}"
    body = json.dumps(payload).encode("utf-8") if payload is not None else b""
    req = Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8")), resp.status
    except Exception as e:
        return json.loads(e.read().decode("utf-8")), e.code


class TestPortalImportDevcontainerPathEndpoint:
    """Tests for POST /forgekeeper/import-devcontainer-path."""

    def test_valid_devcontainer_path(self, server, tmp_path):
        """Path import with a valid devcontainer.json should return success with mapping."""
        devcontainer = {
            "features": {
                "ghcr.io/devcontainers/features/python:1": {"version": "3.11"},
                "ghcr.io/devcontainers/features/go:1": {},
            },
            "forwardPorts": [8080],
            "remoteEnv": {"APP_ENV": "dev"},
        }
        f = tmp_path / "devcontainer.json"
        f.write_text(json.dumps(devcontainer))

        data, status = _post_json(server, "/forgekeeper/import-devcontainer-path", {"path": str(f)})

        assert status == 200
        assert data["success"] is True
        mapping = data["mapping"]
        assert "python" in mapping["languages"]
        assert "go" in mapping["languages"]
        assert mapping["ports"] == [8080]
        assert mapping["env_vars"] == {"APP_ENV": "dev"}

    def test_missing_file_returns_error(self, server):
        """Path import with a non-existent file should return an error."""
        data, status = _post_json(
            server,
            "/forgekeeper/import-devcontainer-path",
            {"path": "/tmp/does_not_exist_devcontainer.json"},
        )

        assert status == 404
        assert data["success"] is False
        assert any("not found" in e.lower() for e in data["errors"])

    def test_invalid_json_file_returns_error(self, server, tmp_path):
        """Path import with a file containing invalid JSON should return an error."""
        f = tmp_path / "bad.json"
        f.write_text("{ this is not valid json !!!")

        data, status = _post_json(server, "/forgekeeper/import-devcontainer-path", {"path": str(f)})

        assert data["success"] is False
        assert len(data["errors"]) > 0

    def test_no_path_provided_returns_error(self, server):
        """Path import with no 'path' key in body should return an error."""
        data, status = _post_json(server, "/forgekeeper/import-devcontainer-path", {})

        assert status == 400
        assert data["success"] is False
        assert any("no path" in e.lower() for e in data["errors"])

    def test_empty_path_returns_error(self, server):
        """Path import with an empty string path should return an error."""
        data, status = _post_json(server, "/forgekeeper/import-devcontainer-path", {"path": ""})

        assert status == 400
        assert data["success"] is False
        assert any("no path" in e.lower() for e in data["errors"])
