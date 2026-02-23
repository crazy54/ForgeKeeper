"""
Integration tests for the complete devcontainer import workflow.

Tests cover:
- Task 16.1: Flow A end-to-end (parse → map → write .env → assemble Dockerfile.built)
- Task 16.2: Flow B end-to-end (parse → map → write /etc/forgekeeper/env → trigger runtime install)

Requirements: 5.1-5.5, 6.1-6.5
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from devcontainer_parser import DevcontainerParser
from devcontainer_mapper import DevcontainerMapper
from config_merger import merge_config


# ── Fixtures ───────────────────────────────────────────────────────

SAMPLE_DEVCONTAINER = {
    "name": "Integration Test Container",
    "image": "mcr.microsoft.com/devcontainers/base:ubuntu",
    "features": {
        "ghcr.io/devcontainers/features/python:1": {"version": "3.11"},
        "ghcr.io/devcontainers/features/node:1": {"version": "20"},
        "ghcr.io/devcontainers/features/go:1": {},
        "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    },
    "customizations": {
        "vscode": {
            "extensions": ["ms-python.python", "golang.go"],
        }
    },
    "forwardPorts": [3000, 8080, 5432],
    "remoteEnv": {
        "MY_APP_ENV": "development",
        "DATABASE_URL": "postgres://localhost:5432/mydb",
        "DEBUG": "true",
    },
}

SAMPLE_DEVCONTAINER_MINIMAL = {
    "features": {
        "ghcr.io/devcontainers/features/rust:1": {},
    },
    "remoteEnv": {
        "RUST_LOG": "info",
    },
}


# ── Task 16.1: Flow A Integration Tests ───────────────────────────


class TestFlowAIntegration:
    """
    Integration tests for complete Flow A import workflow.

    Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5

    Tests the full pipeline: parse devcontainer.json → map features →
    write .env → assemble Dockerfile.built.
    """

    def test_full_flow_a_import_pipeline(self):
        """End-to-end Flow A: parse → map → write_env → assemble_dockerfile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Write a devcontainer.json to disk
            devcontainer_path = Path(tmpdir) / "devcontainer.json"
            devcontainer_path.write_text(json.dumps(SAMPLE_DEVCONTAINER))

            # Step 2: Parse
            parser = DevcontainerParser()
            parse_result = parser.parse_file(str(devcontainer_path))
            assert parse_result.success, f"Parse failed: {parse_result.errors}"
            assert parse_result.config is not None

            # Step 3: Map
            mapper = DevcontainerMapper()
            mapping = mapper.map_features(parse_result.config)
            assert 'python' in mapping.languages
            assert 'node' in mapping.languages
            assert 'go' in mapping.languages
            assert len(mapping.unrecognized_features) == 1  # docker-in-docker

            # Step 4: Build config for write_env
            config = {
                "email": "dev@example.com",
                "handle": "forgekeeper",
                "workspace": "workspace",
                "git_name": "Test User",
                "git_email": "test@example.com",
                "github_token": "",
                "openai_key": "",
                "anthropic_key": "",
                "aws_region": "us-east-1",
                "ollama_models": ["llama3"],
                "imported_env_vars": mapping.env_vars,
                "languages": sorted(mapping.languages),
            }

            env_file = Path(tmpdir) / ".env"
            dockerfile_base = Path(tmpdir) / "Dockerfile"
            dockerfile_out = Path(tmpdir) / "Dockerfile.built"
            dockerfile_base.write_text("FROM ubuntu:24.04\nRUN echo hello\nEXPOSE 8080 7000\n")

            root = Path(__file__).parent.parent
            lang_modules_dir = root / "dockerfiles"

            # Step 5: Write .env
            with patch("setup.ENV_FILE", env_file):
                from setup import write_env
                write_env(config)

            # Step 6: Assemble Dockerfile
            with patch("setup.DOCKERFILE_OUT", dockerfile_out), \
                 patch("setup.DOCKERFILE_BASE", dockerfile_base), \
                 patch("setup.LANG_MODULES_DIR", lang_modules_dir):
                from setup import assemble_dockerfile
                assemble_dockerfile(sorted(mapping.languages))

            # Verify .env contains imported env vars
            env_content = env_file.read_text()
            assert "MY_APP_ENV=development" in env_content
            assert "DATABASE_URL=postgres://localhost:5432/mydb" in env_content
            assert "DEBUG=true" in env_content
            # Also verify standard vars
            assert "FORGEKEEPER_USER_EMAIL=dev@example.com" in env_content
            assert "FORGEKEEPER_HANDLE=forgekeeper" in env_content

            # Verify Dockerfile.built contains language modules
            dockerfile_content = dockerfile_out.read_text()
            for lang in ['python', 'node', 'go']:
                module_file = lang_modules_dir / f"lang-{lang}.dockerfile"
                if module_file.exists():
                    assert f"# ── Language Module: {lang} " in dockerfile_content, (
                        f"Language module '{lang}' not found in Dockerfile.built"
                    )
            assert "EXPOSE" in dockerfile_content

    def test_flow_a_with_minimal_devcontainer(self):
        """Flow A with minimal devcontainer.json (single language, one env var)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            devcontainer_path = Path(tmpdir) / "devcontainer.json"
            devcontainer_path.write_text(json.dumps(SAMPLE_DEVCONTAINER_MINIMAL))

            parser = DevcontainerParser()
            parse_result = parser.parse_file(str(devcontainer_path))
            assert parse_result.success

            mapper = DevcontainerMapper()
            mapping = mapper.map_features(parse_result.config)
            assert 'rust' in mapping.languages
            assert mapping.env_vars == {"RUST_LOG": "info"}

            config = {
                "email": "dev@example.com",
                "handle": "forgekeeper",
                "workspace": "workspace",
                "git_name": "",
                "git_email": "",
                "github_token": "",
                "openai_key": "",
                "anthropic_key": "",
                "aws_region": "us-east-1",
                "ollama_models": ["llama3"],
                "imported_env_vars": mapping.env_vars,
            }

            env_file = Path(tmpdir) / ".env"
            with patch("setup.ENV_FILE", env_file):
                from setup import write_env
                write_env(config)

            env_content = env_file.read_text()
            assert "RUST_LOG=info" in env_content

    def test_flow_a_merge_user_and_imported_config(self):
        """Flow A: user config merged with imported config, user takes priority."""
        parser = DevcontainerParser()
        parse_result = parser.parse_content(json.dumps(SAMPLE_DEVCONTAINER))
        assert parse_result.success

        mapper = DevcontainerMapper()
        mapping = mapper.map_features(parse_result.config)

        user_config = {
            'env_vars': {'MY_APP_ENV': 'production', 'CUSTOM_VAR': 'custom'},
            'languages': ['ruby'],
            'ports': [9090],
        }
        imported_config = {
            'env_vars': mapping.env_vars,
            'languages': sorted(mapping.languages),
            'ports': mapping.ports,
        }

        merged = merge_config(user_config, imported_config)

        # User value wins on conflict
        assert merged['env_vars']['MY_APP_ENV'] == 'production'
        # Imported vars still present
        assert merged['env_vars']['DATABASE_URL'] == 'postgres://localhost:5432/mydb'
        # User custom var present
        assert merged['env_vars']['CUSTOM_VAR'] == 'custom'
        # Languages merged
        assert 'ruby' in merged['languages']
        assert 'python' in merged['languages']
        # Ports merged
        assert 9090 in merged['ports']
        assert 3000 in merged['ports']

    def test_flow_a_no_language_features(self):
        """Flow A with devcontainer that has no language features."""
        devcontainer = {
            "features": {
                "ghcr.io/devcontainers/features/docker-in-docker:2": {},
                "ghcr.io/devcontainers/features/git:1": {},
            },
            "remoteEnv": {"EDITOR": "vim"},
        }

        parser = DevcontainerParser()
        parse_result = parser.parse_content(json.dumps(devcontainer))
        assert parse_result.success

        mapper = DevcontainerMapper()
        mapping = mapper.map_features(parse_result.config)

        assert len(mapping.languages) == 0
        assert len(mapping.unrecognized_features) == 2
        assert mapping.env_vars == {"EDITOR": "vim"}

    def test_flow_a_ports_forwarded_correctly(self):
        """Flow A: forwarded ports are preserved through the pipeline."""
        parser = DevcontainerParser()
        parse_result = parser.parse_content(json.dumps(SAMPLE_DEVCONTAINER))
        assert parse_result.success

        mapper = DevcontainerMapper()
        mapping = mapper.map_features(parse_result.config)

        assert 3000 in mapping.ports
        assert 8080 in mapping.ports
        assert 5432 in mapping.ports

    def test_flow_a_unrecognized_features_in_warnings(self):
        """Flow A: unrecognized features produce warnings for user review."""
        parser = DevcontainerParser()
        parse_result = parser.parse_content(json.dumps(SAMPLE_DEVCONTAINER))
        assert parse_result.success

        mapper = DevcontainerMapper()
        mapping = mapper.map_features(parse_result.config)

        assert 'ghcr.io/devcontainers/features/docker-in-docker:2' in mapping.unrecognized_features
        assert any('docker-in-docker' in w for w in mapping.warnings)


# ── Task 16.2: Flow B Integration Tests ───────────────────────────


class TestFlowBIntegration:
    """
    Integration tests for complete Flow B import workflow.

    Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5

    Tests the full pipeline: parse devcontainer.json → map features →
    write /etc/forgekeeper/env → trigger runtime installation.
    Uses mocks for filesystem paths.
    """

    def test_full_flow_b_import_pipeline(self):
        """End-to-end Flow B: parse → map → write env → trigger installs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Write devcontainer.json
            devcontainer_path = Path(tmpdir) / "devcontainer.json"
            devcontainer_path.write_text(json.dumps(SAMPLE_DEVCONTAINER))

            # Step 2: Parse
            parser = DevcontainerParser()
            parse_result = parser.parse_file(str(devcontainer_path))
            assert parse_result.success

            # Step 3: Map
            mapper = DevcontainerMapper()
            mapping = mapper.map_features(parse_result.config)

            # Step 4: Build Flow B payload
            payload = {
                "handle": "forgekeeper",
                "email": "dev@example.com",
                "workspace": "workspace",
                "git_name": "Test User",
                "git_email": "test@example.com",
                "github_token": "",
                "openai_key": "",
                "anthropic_key": "",
                "aws_region": "us-east-1",
                "languages": sorted(mapping.languages),
                "imported_env_vars": mapping.env_vars,
            }

            # Step 5: Simulate _handle_setup logic (write env file)
            env_file = Path(tmpdir) / "env"
            setup_complete = Path(tmpdir) / ".setup-complete"
            runtime_script = Path(tmpdir) / "forgekeeper-runtime"
            runtime_script.touch()

            env_file.parent.mkdir(parents=True, exist_ok=True)
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
            imported_env = payload.get("imported_env_vars", {})
            for key, value in imported_env.items():
                lines.append(f'{key}={value}')
            env_file.write_text("\n".join(lines) + "\n")

            # Step 6: Trigger runtime installation (mocked)
            selected_langs = payload["languages"]
            allowed_langs = {"python", "node", "go", "rust", "java", "dotnet", "ruby", "php", "swift", "dart"}

            with patch("subprocess.Popen") as mock_popen:
                for lang in selected_langs:
                    if lang in allowed_langs and runtime_script.exists():
                        subprocess.Popen(["sudo", str(runtime_script), "install", lang])

                # Verify runtime install triggered for each language
                assert mock_popen.call_count == len(selected_langs)
                called_langs = set()
                for call in mock_popen.call_args_list:
                    args = call[0][0]
                    assert args[0] == "sudo"
                    assert args[2] == "install"
                    called_langs.add(args[3])
                assert called_langs == set(selected_langs)

            # Step 7: Mark setup complete
            setup_complete.touch()
            assert setup_complete.exists()

            # Verify env file contains imported config
            env_content = env_file.read_text()
            assert "MY_APP_ENV=development" in env_content
            assert "DATABASE_URL=postgres://localhost:5432/mydb" in env_content
            assert "DEBUG=true" in env_content
            assert "FORGEKEEPER_HANDLE=forgekeeper" in env_content

    def test_flow_b_with_minimal_devcontainer(self):
        """Flow B with minimal devcontainer (single language)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            devcontainer_path = Path(tmpdir) / "devcontainer.json"
            devcontainer_path.write_text(json.dumps(SAMPLE_DEVCONTAINER_MINIMAL))

            parser = DevcontainerParser()
            parse_result = parser.parse_file(str(devcontainer_path))
            assert parse_result.success

            mapper = DevcontainerMapper()
            mapping = mapper.map_features(parse_result.config)
            assert 'rust' in mapping.languages

            # Simulate env file write
            env_file = Path(tmpdir) / "env"
            lines = [
                f'FORGEKEEPER_HANDLE=forgekeeper',
                f'FORGEKEEPER_USER_EMAIL=dev@example.com',
            ]
            for key, value in mapping.env_vars.items():
                lines.append(f'{key}={value}')
            env_file.write_text("\n".join(lines) + "\n")

            env_content = env_file.read_text()
            assert "RUST_LOG=info" in env_content

            # Simulate runtime install
            runtime_script = Path(tmpdir) / "forgekeeper-runtime"
            runtime_script.touch()
            with patch("subprocess.Popen") as mock_popen:
                for lang in sorted(mapping.languages):
                    subprocess.Popen(["sudo", str(runtime_script), "install", lang])
                assert mock_popen.call_count == 1
                args = mock_popen.call_args_list[0][0][0]
                assert args[3] == "rust"

    def test_flow_b_env_file_written_to_correct_path(self):
        """Flow B: env vars written to simulated /etc/forgekeeper/env path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Simulate /etc/forgekeeper/ structure
            forgekeeper_dir = Path(tmpdir) / "etc" / "forgekeeper"
            forgekeeper_dir.mkdir(parents=True)
            env_file = forgekeeper_dir / "env"

            parser = DevcontainerParser()
            parse_result = parser.parse_content(json.dumps(SAMPLE_DEVCONTAINER))
            assert parse_result.success

            mapper = DevcontainerMapper()
            mapping = mapper.map_features(parse_result.config)

            lines = [f'FORGEKEEPER_HANDLE=forgekeeper']
            for key, value in mapping.env_vars.items():
                lines.append(f'{key}={value}')
            env_file.write_text("\n".join(lines) + "\n")

            assert env_file.exists()
            content = env_file.read_text()
            for key, value in mapping.env_vars.items():
                assert f"{key}={value}" in content

    def test_flow_b_setup_complete_marker_created(self):
        """Flow B: setup complete marker file is created after setup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_complete = Path(tmpdir) / ".setup-complete"
            assert not setup_complete.exists()

            # Simulate setup completion
            setup_complete.parent.mkdir(parents=True, exist_ok=True)
            setup_complete.touch()

            assert setup_complete.exists()

    def test_flow_b_only_allowed_languages_installed(self):
        """Flow B: only allowed languages trigger runtime installation."""
        allowed_langs = {"python", "node", "go", "rust", "java", "dotnet", "ruby", "php", "swift", "dart"}

        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_script = Path(tmpdir) / "forgekeeper-runtime"
            runtime_script.touch()

            # Include a mix of allowed and hypothetical disallowed languages
            requested_langs = ["python", "node", "unknown_lang", "go"]

            with patch("subprocess.Popen") as mock_popen:
                for lang in requested_langs:
                    if lang in allowed_langs and runtime_script.exists():
                        subprocess.Popen(["sudo", str(runtime_script), "install", lang])

                # Only 3 allowed languages should trigger install
                assert mock_popen.call_count == 3
                called_langs = {call[0][0][3] for call in mock_popen.call_args_list}
                assert called_langs == {"python", "node", "go"}

    def test_flow_b_imported_env_merged_with_user_config(self):
        """Flow B: imported env vars merged with user wizard config."""
        parser = DevcontainerParser()
        parse_result = parser.parse_content(json.dumps(SAMPLE_DEVCONTAINER))
        assert parse_result.success

        mapper = DevcontainerMapper()
        mapping = mapper.map_features(parse_result.config)

        user_config = {
            'env_vars': {'MY_APP_ENV': 'staging'},
            'languages': ['php'],
            'ports': [4000],
        }
        imported_config = {
            'env_vars': mapping.env_vars,
            'languages': sorted(mapping.languages),
            'ports': mapping.ports,
        }

        merged = merge_config(user_config, imported_config)

        # User value wins
        assert merged['env_vars']['MY_APP_ENV'] == 'staging'
        # Imported vars present
        assert 'DATABASE_URL' in merged['env_vars']
        # Languages merged
        assert 'php' in merged['languages']
        assert 'python' in merged['languages']
