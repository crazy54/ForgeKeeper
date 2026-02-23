#!/usr/bin/env python3
"""
Unit tests for devcontainer_parser module.

Tests JSON parsing, validation, and error handling.
"""
import json
import pytest
import tempfile
from pathlib import Path
import sys

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from devcontainer_parser import DevcontainerParser, ParseResult, DevcontainerConfig


class TestDevcontainerParser:
    """Test suite for DevcontainerParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = DevcontainerParser()
    
    def test_parse_valid_minimal_json(self):
        """Test parsing a minimal valid devcontainer.json."""
        content = json.dumps({
            "image": "mcr.microsoft.com/devcontainers/python:3.11"
        })
        
        result = self.parser.parse_content(content)
        
        assert result.success is True
        assert result.config is not None
        assert result.config.image == "mcr.microsoft.com/devcontainers/python:3.11"
        assert result.config.features == {}
        assert result.config.forward_ports == []
        assert len(result.errors) == 0
    
    def test_parse_valid_complete_json(self):
        """Test parsing a complete devcontainer.json with all properties."""
        content = json.dumps({
            "name": "My Dev Container",
            "image": "mcr.microsoft.com/devcontainers/base:ubuntu",
            "features": {
                "ghcr.io/devcontainers/features/python:1": {
                    "version": "3.11"
                },
                "ghcr.io/devcontainers/features/node:1": {
                    "version": "20"
                }
            },
            "customizations": {
                "vscode": {
                    "extensions": ["ms-python.python"]
                }
            },
            "forwardPorts": [3000, 8080],
            "remoteEnv": {
                "MY_VAR": "value",
                "ANOTHER_VAR": "another_value"
            }
        })
        
        result = self.parser.parse_content(content)
        
        assert result.success is True
        assert result.config is not None
        assert result.config.image == "mcr.microsoft.com/devcontainers/base:ubuntu"
        assert len(result.config.features) == 2
        assert "ghcr.io/devcontainers/features/python:1" in result.config.features
        assert result.config.features["ghcr.io/devcontainers/features/python:1"]["version"] == "3.11"
        assert result.config.forward_ports == [3000, 8080]
        assert result.config.remote_env["MY_VAR"] == "value"
        assert len(result.errors) == 0
    
    def test_parse_invalid_json_syntax(self):
        """Test parsing invalid JSON returns descriptive error."""
        content = '{"image": "test", invalid json}'
        
        result = self.parser.parse_content(content)
        
        assert result.success is False
        assert result.config is None
        assert len(result.errors) > 0
        assert "Invalid JSON syntax" in result.errors[0]
    
    def test_parse_non_object_json(self):
        """Test parsing JSON that is not an object."""
        content = '["array", "not", "object"]'
        
        result = self.parser.parse_content(content)
        
        assert result.success is False
        assert result.config is None
        assert len(result.errors) > 0
        assert "root must be an object" in result.errors[0]
    
    def test_parse_empty_json_object(self):
        """Test parsing empty JSON object."""
        content = '{}'
        
        result = self.parser.parse_content(content)
        
        assert result.success is True
        assert result.config is not None
        assert result.config.features == {}
        assert result.config.forward_ports == []
        assert result.config.remote_env == {}
    
    def test_parse_file_success(self):
        """Test parsing a valid file from disk."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "image": "python:3.11",
                "features": {
                    "ghcr.io/devcontainers/features/python:1": {}
                }
            }, f)
            temp_path = f.name
        
        try:
            result = self.parser.parse_file(temp_path)
            
            assert result.success is True
            assert result.config is not None
            assert result.config.image == "python:3.11"
        finally:
            Path(temp_path).unlink()
    
    def test_parse_file_not_found(self):
        """Test parsing non-existent file returns error."""
        result = self.parser.parse_file('/nonexistent/path/devcontainer.json')
        
        assert result.success is False
        assert result.config is None
        assert len(result.errors) > 0
        assert "File not found" in result.errors[0]
    
    def test_parse_file_invalid_json(self):
        """Test parsing file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')
            temp_path = f.name
        
        try:
            result = self.parser.parse_file(temp_path)
            
            assert result.success is False
            assert result.config is None
            assert len(result.errors) > 0
        finally:
            Path(temp_path).unlink()
    
    def test_validate_schema_valid(self):
        """Test schema validation with valid data."""
        data = {
            "image": "python:3.11",
            "features": {},
            "forwardPorts": [3000]
        }
        
        errors = self.parser.validate_schema(data)
        
        assert len(errors) == 0
    
    def test_validate_schema_invalid_features_type(self):
        """Test schema validation catches invalid features type."""
        data = {
            "features": "should be object not string"
        }
        
        errors = self.parser.validate_schema(data)
        
        assert len(errors) > 0
        assert "features" in errors[0].lower()
    
    def test_validate_schema_invalid_ports_type(self):
        """Test schema validation catches invalid forwardPorts type."""
        data = {
            "forwardPorts": "should be array not string"
        }
        
        errors = self.parser.validate_schema(data)
        
        assert len(errors) > 0
        assert "forwardPorts" in errors[0].lower() or "forward" in errors[0].lower()
    
    def test_extract_ports_from_integers(self):
        """Test port extraction from integer values."""
        content = json.dumps({
            "forwardPorts": [3000, 8080, 5432]
        })
        
        result = self.parser.parse_content(content)
        
        assert result.success is True
        assert result.config.forward_ports == [3000, 8080, 5432]
    
    def test_extract_ports_from_strings(self):
        """Test port extraction from string values."""
        content = json.dumps({
            "forwardPorts": ["3000", "8080"]
        })
        
        result = self.parser.parse_content(content)
        
        assert result.success is True
        assert result.config.forward_ports == [3000, 8080]
    
    def test_extract_ports_mixed_types(self):
        """Test port extraction from mixed integer and string values."""
        content = json.dumps({
            "forwardPorts": [3000, "8080", 5432]
        })
        
        result = self.parser.parse_content(content)
        
        assert result.success is True
        assert result.config.forward_ports == [3000, 8080, 5432]
    
    def test_extract_ports_invalid_values_skipped(self):
        """Test that invalid port values are skipped."""
        content = json.dumps({
            "forwardPorts": [3000, "invalid", None, 8080]
        })
        
        result = self.parser.parse_content(content)
        
        assert result.success is True
        # Invalid values should be skipped
        assert 3000 in result.config.forward_ports
        assert 8080 in result.config.forward_ports
        assert len(result.config.forward_ports) == 2
    
    def test_parse_with_dockerfile(self):
        """Test parsing devcontainer with dockerfile instead of image."""
        content = json.dumps({
            "dockerfile": "Dockerfile",
            "features": {}
        })
        
        result = self.parser.parse_content(content)
        
        assert result.success is True
        assert result.config.dockerfile == "Dockerfile"
        assert result.config.image is None
    
    def test_parse_preserves_raw_data(self):
        """Test that raw data is preserved in config."""
        data = {
            "image": "python:3.11",
            "features": {"test": {}},
            "customProperty": "customValue"
        }
        content = json.dumps(data)
        
        result = self.parser.parse_content(content)
        
        assert result.success is True
        assert result.config.raw == data
        assert result.config.raw["customProperty"] == "customValue"

    class TestExtractionMethods:
        """Tests for dedicated configuration extraction methods."""

        def setup_method(self):
            self.parser = DevcontainerParser()

        # _extract_features tests

        def test_extract_features_returns_dict(self):
            """Test _extract_features returns features dict from data."""
            data = {"features": {"ghcr.io/devcontainers/features/python:1": {"version": "3.11"}}}
            assert self.parser._extract_features(data) == data["features"]

        def test_extract_features_missing_returns_empty(self):
            """Test _extract_features returns empty dict when features absent."""
            assert self.parser._extract_features({}) == {}

        def test_extract_features_non_dict_returns_empty(self):
            """Test _extract_features returns empty dict for non-dict value."""
            assert self.parser._extract_features({"features": "bad"}) == {}

        # _extract_customizations tests

        def test_extract_customizations_returns_dict(self):
            """Test _extract_customizations returns customizations dict."""
            data = {"customizations": {"vscode": {"extensions": ["ms-python.python"]}}}
            assert self.parser._extract_customizations(data) == data["customizations"]

        def test_extract_customizations_missing_returns_empty(self):
            """Test _extract_customizations returns empty dict when absent."""
            assert self.parser._extract_customizations({}) == {}

        def test_extract_customizations_non_dict_returns_empty(self):
            """Test _extract_customizations returns empty dict for non-dict value."""
            assert self.parser._extract_customizations({"customizations": 42}) == {}

        # _extract_env tests

        def test_extract_env_returns_string_values(self):
            """Test _extract_env returns remoteEnv key-value pairs."""
            data = {"remoteEnv": {"MY_VAR": "value", "OTHER": "val2"}}
            assert self.parser._extract_env(data) == {"MY_VAR": "value", "OTHER": "val2"}

        def test_extract_env_missing_returns_empty(self):
            """Test _extract_env returns empty dict when remoteEnv absent."""
            assert self.parser._extract_env({}) == {}

        def test_extract_env_filters_non_string_values(self):
            """Test _extract_env filters out non-string values."""
            data = {"remoteEnv": {"GOOD": "value", "BAD": 123, "ALSO_BAD": None}}
            assert self.parser._extract_env(data) == {"GOOD": "value"}

        def test_extract_env_non_dict_returns_empty(self):
            """Test _extract_env returns empty dict for non-dict remoteEnv."""
            assert self.parser._extract_env({"remoteEnv": "bad"}) == {}

        # _extract_image_config tests

        def test_extract_image_config_with_image(self):
            """Test _extract_image_config returns image string."""
            data = {"image": "python:3.11"}
            image, dockerfile = self.parser._extract_image_config(data)
            assert image == "python:3.11"
            assert dockerfile is None

        def test_extract_image_config_with_dockerfile(self):
            """Test _extract_image_config returns dockerfile string."""
            data = {"dockerfile": "Dockerfile.dev"}
            image, dockerfile = self.parser._extract_image_config(data)
            assert image is None
            assert dockerfile == "Dockerfile.dev"

        def test_extract_image_config_with_both(self):
            """Test _extract_image_config returns both when present."""
            data = {"image": "base:latest", "dockerfile": "Dockerfile"}
            image, dockerfile = self.parser._extract_image_config(data)
            assert image == "base:latest"
            assert dockerfile == "Dockerfile"

        def test_extract_image_config_missing_returns_none(self):
            """Test _extract_image_config returns None tuple when absent."""
            image, dockerfile = self.parser._extract_image_config({})
            assert image is None
            assert dockerfile is None

        def test_extract_image_config_non_string_returns_none(self):
            """Test _extract_image_config returns None for non-string values."""
            data = {"image": 123, "dockerfile": True}
            image, dockerfile = self.parser._extract_image_config(data)
            assert image is None
            assert dockerfile is None

        # Integration: extraction methods used via parse_content

        def test_parse_content_uses_extraction_methods(self):
            """Test parse_content correctly delegates to extraction methods."""
            content = json.dumps({
                "features": {"ghcr.io/devcontainers/features/go:1": {}},
                "customizations": {"vscode": {"settings": {}}},
                "forwardPorts": [9090],
                "remoteEnv": {"GOPATH": "/go"},
                "image": "golang:1.21",
                "dockerfile": "Dockerfile.go"
            })
            result = self.parser.parse_content(content)

            assert result.success is True
            assert result.config.features == {"ghcr.io/devcontainers/features/go:1": {}}
            assert result.config.customizations == {"vscode": {"settings": {}}}
            assert result.config.forward_ports == [9090]
            assert result.config.remote_env == {"GOPATH": "/go"}
            assert result.config.image == "golang:1.21"
            assert result.config.dockerfile == "Dockerfile.go"


class TestParserEdgeCases:
    """Edge case tests for DevcontainerParser.

    Validates: Requirements 1.5, 9.1, 9.2
    """

    def setup_method(self):
        self.parser = DevcontainerParser()

    # --- Empty devcontainer.json ---

    def test_empty_object_succeeds_with_defaults(self):
        """Empty {} should parse successfully with all default empty values."""
        result = self.parser.parse_content('{}')

        assert result.success is True
        assert result.config is not None
        assert result.config.features == {}
        assert result.config.customizations == {}
        assert result.config.forward_ports == []
        assert result.config.remote_env == {}
        assert result.config.image is None
        assert result.config.dockerfile is None
        assert result.config.raw == {}
        assert result.errors == []

    # --- Missing optional properties ---

    def test_no_features_property(self):
        """Config without features should succeed with empty features dict."""
        result = self.parser.parse_content(json.dumps({"image": "ubuntu:22.04"}))
        assert result.success is True
        assert result.config.features == {}

    def test_no_customizations_property(self):
        """Config without customizations should succeed with empty dict."""
        result = self.parser.parse_content(json.dumps({"image": "ubuntu:22.04"}))
        assert result.success is True
        assert result.config.customizations == {}

    def test_no_ports_property(self):
        """Config without forwardPorts should succeed with empty list."""
        result = self.parser.parse_content(json.dumps({"image": "ubuntu:22.04"}))
        assert result.success is True
        assert result.config.forward_ports == []

    def test_no_env_property(self):
        """Config without remoteEnv should succeed with empty dict."""
        result = self.parser.parse_content(json.dumps({"image": "ubuntu:22.04"}))
        assert result.success is True
        assert result.config.remote_env == {}

    def test_no_image_no_dockerfile(self):
        """Config with neither image nor dockerfile should succeed."""
        result = self.parser.parse_content(json.dumps({"name": "test"}))
        assert result.success is True
        assert result.config.image is None
        assert result.config.dockerfile is None

    def test_only_name_property(self):
        """Config with only a name property should succeed with all defaults."""
        result = self.parser.parse_content(json.dumps({"name": "My Container"}))
        assert result.success is True
        assert result.config.features == {}
        assert result.config.customizations == {}
        assert result.config.forward_ports == []
        assert result.config.remote_env == {}
        assert result.config.image is None
        assert result.config.dockerfile is None

    # --- Malformed JSON error messages ---

    def test_malformed_json_includes_line_info(self):
        """Malformed JSON error should include line number."""
        result = self.parser.parse_content('{\n  "image": bad\n}')
        assert result.success is False
        assert len(result.errors) == 1
        assert "line" in result.errors[0].lower()

    def test_malformed_json_includes_column_info(self):
        """Malformed JSON error should include column number."""
        result = self.parser.parse_content('{"image": }')
        assert result.success is False
        assert "column" in result.errors[0].lower()

    def test_malformed_json_trailing_comma(self):
        """Trailing comma should produce descriptive error."""
        result = self.parser.parse_content('{"image": "test",}')
        assert result.success is False
        assert "Invalid JSON syntax" in result.errors[0]

    def test_malformed_json_unclosed_brace(self):
        """Unclosed brace should produce descriptive error."""
        result = self.parser.parse_content('{"image": "test"')
        assert result.success is False
        assert "Invalid JSON syntax" in result.errors[0]

    def test_malformed_json_empty_string(self):
        """Empty string should produce descriptive error."""
        result = self.parser.parse_content('')
        assert result.success is False
        assert len(result.errors) > 0

    # --- Special characters in env var values ---

    def test_env_var_with_spaces(self):
        """Env var values with spaces should be preserved."""
        result = self.parser.parse_content(json.dumps({
            "remoteEnv": {"PATH_EXT": "/usr/local/bin:/usr/bin"}
        }))
        assert result.success is True
        assert result.config.remote_env["PATH_EXT"] == "/usr/local/bin:/usr/bin"

    def test_env_var_with_special_characters(self):
        """Env var values with special chars (=, quotes, newlines) should be preserved."""
        result = self.parser.parse_content(json.dumps({
            "remoteEnv": {
                "CONN_STR": "host=localhost;port=5432;db=test",
                "GREETING": "Hello \"World\"",
                "MULTILINE": "line1\nline2"
            }
        }))
        assert result.success is True
        assert result.config.remote_env["CONN_STR"] == "host=localhost;port=5432;db=test"
        assert result.config.remote_env["GREETING"] == 'Hello "World"'
        assert result.config.remote_env["MULTILINE"] == "line1\nline2"

    def test_env_var_with_unicode(self):
        """Env var values with unicode characters should be preserved."""
        result = self.parser.parse_content(json.dumps({
            "remoteEnv": {"LANG": "en_US.UTF-8", "EMOJI": "🚀"}
        }))
        assert result.success is True
        assert result.config.remote_env["EMOJI"] == "🚀"

    def test_env_var_empty_value(self):
        """Env var with empty string value should be preserved."""
        result = self.parser.parse_content(json.dumps({
            "remoteEnv": {"EMPTY": ""}
        }))
        assert result.success is True
        assert result.config.remote_env["EMPTY"] == ""

    # --- Null values in various properties ---

    def test_null_image_rejected_by_schema(self):
        """Null image value should be rejected by schema validation."""
        result = self.parser.parse_content(json.dumps({"image": None}))
        assert result.success is False
        assert any("image" in e.lower() for e in result.errors)

    def test_null_dockerfile_rejected_by_schema(self):
        """Null dockerfile value should be rejected by schema validation."""
        result = self.parser.parse_content(json.dumps({"dockerfile": None}))
        assert result.success is False
        assert any("dockerfile" in e.lower() for e in result.errors)

    def test_null_in_forward_ports_skipped(self):
        """Null values in forwardPorts should be skipped (null is allowed by schema items)."""
        result = self.parser.parse_content(json.dumps({
            "forwardPorts": [3000, None, 8080]
        }))
        assert result.success is True
        assert result.config.forward_ports == [3000, 8080]

    def test_null_env_var_value_rejected_by_schema(self):
        """Null env var values should be rejected by schema validation."""
        result = self.parser.parse_content(json.dumps({
            "remoteEnv": {"GOOD": "value", "BAD": None}
        }))
        assert result.success is False
        assert any("remoteenv" in e.lower() or "bad" in e.lower() for e in result.errors)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
