#!/usr/bin/env python3
"""
Unit tests for security_utils module.

Validates: Requirements 7.5, 9.1
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from security_utils import (
    validate_path,
    validate_file_size,
    is_sensitive,
    mask_value,
    validate_ports,
    PortValidationResult,
    MAX_FILE_SIZE,
    SENSITIVE_KEYS,
)


class TestValidatePath:
    """Tests for validate_path() - path traversal prevention."""

    def test_valid_path_within_base(self, tmp_path):
        """Path inside base directory should be valid."""
        child = tmp_path / "subdir" / "file.json"
        child.parent.mkdir(parents=True, exist_ok=True)
        child.touch()
        assert validate_path(str(child), str(tmp_path)) is True

    def test_base_dir_itself_is_valid(self, tmp_path):
        """The base directory itself should be valid."""
        assert validate_path(str(tmp_path), str(tmp_path)) is True

    def test_path_traversal_rejected(self, tmp_path):
        """Path with .. escaping base directory should be rejected."""
        escaped = str(tmp_path / ".." / ".." / "etc" / "passwd")
        assert validate_path(escaped, str(tmp_path)) is False

    def test_relative_path_traversal_rejected(self, tmp_path):
        """Relative path traversal should be rejected."""
        assert validate_path("../../etc/passwd", str(tmp_path)) is False

    def test_sibling_directory_rejected(self, tmp_path):
        """Path to a sibling directory should be rejected."""
        sibling = tmp_path.parent / "sibling"
        assert validate_path(str(sibling), str(tmp_path)) is False

    def test_nested_valid_path(self, tmp_path):
        """Deeply nested path within base should be valid."""
        deep = tmp_path / "a" / "b" / "c" / "d" / "file.json"
        assert validate_path(str(deep), str(tmp_path)) is True


class TestValidateFileSize:
    """Tests for validate_file_size() - file size enforcement."""

    def test_small_file_passes(self, tmp_path):
        """File under the limit should pass."""
        f = tmp_path / "small.json"
        f.write_text('{"image": "test"}')
        assert validate_file_size(str(f)) is True

    def test_empty_file_passes(self, tmp_path):
        """Empty file should pass."""
        f = tmp_path / "empty.json"
        f.write_text('')
        assert validate_file_size(str(f)) is True

    def test_exact_limit_passes(self, tmp_path):
        """File exactly at the limit should pass."""
        f = tmp_path / "exact.json"
        f.write_bytes(b'x' * MAX_FILE_SIZE)
        assert validate_file_size(str(f)) is True

    def test_over_limit_fails(self, tmp_path):
        """File exceeding the limit should fail."""
        f = tmp_path / "large.json"
        f.write_bytes(b'x' * (MAX_FILE_SIZE + 1))
        assert validate_file_size(str(f)) is False

    def test_nonexistent_file_raises(self, tmp_path):
        """Non-existent file should raise an error."""
        with pytest.raises(FileNotFoundError):
            validate_file_size(str(tmp_path / "missing.json"))


class TestIsSensitive:
    """Tests for is_sensitive() - sensitive variable detection."""

    @pytest.mark.parametrize("key", [
        "API_TOKEN", "MY_SECRET", "DB_PASSWORD", "AUTH_KEY",
        "CREDENTIAL_FILE", "PRIVATE_KEY", "api_key", "auth_token",
    ])
    def test_sensitive_keys_detected(self, key):
        """Keys containing sensitive patterns should be detected."""
        assert is_sensitive(key) is True

    @pytest.mark.parametrize("key", [
        "PATH", "HOME", "LANG", "NODE_ENV", "PYTHON_VERSION",
        "MY_VAR", "PORT", "HOST",
    ])
    def test_non_sensitive_keys_pass(self, key):
        """Normal environment variable names should not be flagged."""
        assert is_sensitive(key) is False

    def test_case_insensitive_matching(self):
        """Detection should be case-insensitive."""
        assert is_sensitive("SECRET") is True
        assert is_sensitive("Secret") is True
        assert is_sensitive("secret") is True

    def test_pattern_as_substring(self):
        """Pattern appearing as substring should be detected."""
        assert is_sensitive("MY_AUTH_HEADER") is True
        assert is_sensitive("github_token_value") is True

    def test_empty_key(self):
        """Empty key should not be sensitive."""
        assert is_sensitive("") is False


class TestMaskValue:
    """Tests for mask_value() - sensitive value masking."""

    def test_short_value_fully_masked(self):
        """Values of 4 chars or fewer should be fully masked."""
        assert mask_value("ab") == "***"
        assert mask_value("abcd") == "***"
        assert mask_value("") == "***"
        assert mask_value("x") == "***"

    def test_longer_value_partially_masked(self):
        """Values longer than 4 chars show first 2 and last 2."""
        assert mask_value("abcde") == "ab***de"
        assert mask_value("my-secret-token") == "my***en"

    def test_exactly_five_chars(self):
        """Five character value should show first 2 and last 2."""
        assert mask_value("12345") == "12***45"

    def test_masked_value_contains_stars(self):
        """Masked output should always contain '***'."""
        assert "***" in mask_value("anything")
        assert "***" in mask_value("ab")

    def test_original_value_not_fully_visible(self):
        """For sensitive values, the full original should not be recoverable."""
        original = "super-secret-password-123"
        masked = mask_value(original)
        assert masked != original
        assert "***" in masked


class TestValidatePorts:
    """Tests for validate_ports() - port range validation.

    Validates: Requirements 8.2
    """

    def test_all_valid_ports(self):
        """All ports in valid range should be returned as valid."""
        result = validate_ports([80, 443, 3000, 8080])
        assert result.valid_ports == [80, 443, 3000, 8080]
        assert result.invalid_ports == []

    def test_all_invalid_ports(self):
        """Ports outside 1-65535 should be returned as invalid."""
        result = validate_ports([0, -1, 65536, 100000])
        assert result.valid_ports == []
        assert result.invalid_ports == [0, -1, 65536, 100000]

    def test_mixed_valid_and_invalid(self):
        """Mixed list should be separated correctly."""
        result = validate_ports([0, 80, -5, 443, 70000, 8080])
        assert result.valid_ports == [80, 443, 8080]
        assert result.invalid_ports == [0, -5, 70000]

    def test_boundary_port_1(self):
        """Port 1 (minimum valid) should be valid."""
        result = validate_ports([1])
        assert result.valid_ports == [1]
        assert result.invalid_ports == []

    def test_boundary_port_65535(self):
        """Port 65535 (maximum valid) should be valid."""
        result = validate_ports([65535])
        assert result.valid_ports == [65535]
        assert result.invalid_ports == []

    def test_boundary_port_0(self):
        """Port 0 should be invalid."""
        result = validate_ports([0])
        assert result.valid_ports == []
        assert result.invalid_ports == [0]

    def test_boundary_port_65536(self):
        """Port 65536 should be invalid."""
        result = validate_ports([65536])
        assert result.valid_ports == []
        assert result.invalid_ports == [65536]

    def test_empty_list(self):
        """Empty input should return empty results."""
        result = validate_ports([])
        assert result.valid_ports == []
        assert result.invalid_ports == []

    def test_negative_ports(self):
        """Negative port numbers should be invalid."""
        result = validate_ports([-1, -100, -65535])
        assert result.valid_ports == []
        assert result.invalid_ports == [-1, -100, -65535]

    def test_returns_port_validation_result(self):
        """Return type should be PortValidationResult."""
        result = validate_ports([80])
        assert isinstance(result, PortValidationResult)

    def test_preserves_order(self):
        """Valid and invalid lists should preserve input order."""
        result = validate_ports([8080, 0, 443, -1, 3000, 70000])
        assert result.valid_ports == [8080, 443, 3000]
        assert result.invalid_ports == [0, -1, 70000]

