#!/usr/bin/env python3
"""
Security Utilities Module

Provides validation and sanitization functions for the devcontainer import feature.
Includes path traversal prevention, file size enforcement, and sensitive variable masking.
"""
from dataclasses import dataclass
from pathlib import Path

# Maximum allowed file size for devcontainer.json uploads (1 MB)
MAX_FILE_SIZE = 1024 * 1024  # 1 MB

# Patterns that indicate sensitive environment variable names
SENSITIVE_KEYS = {
    'token', 'key', 'secret', 'password', 'credential',
    'api_key', 'auth', 'private'
}


def validate_path(path: str, base_dir: str) -> bool:
    """
    Validate that path doesn't escape base directory.

    Prevents path traversal attacks by resolving the path and checking
    it remains within the allowed base directory.

    Args:
        path: User-provided file path to validate
        base_dir: Allowed base directory

    Returns:
        True if path is safe (within base_dir), False otherwise
    """
    resolved = Path(path).resolve()
    base = Path(base_dir).resolve()
    try:
        resolved.relative_to(base)
        return True
    except ValueError:
        return False


def validate_file_size(file_path: str) -> bool:
    """
    Ensure file is not too large.

    Checks that the file at the given path does not exceed MAX_FILE_SIZE.

    Args:
        file_path: Path to the file to check

    Returns:
        True if file size is within the limit, False otherwise
    """
    return Path(file_path).stat().st_size <= MAX_FILE_SIZE


def is_sensitive(key: str) -> bool:
    """
    Check if environment variable key contains sensitive data.

    Performs case-insensitive substring matching against known
    sensitive patterns (token, key, secret, password, etc.).

    Args:
        key: Environment variable name to check

    Returns:
        True if the key matches any sensitive pattern
    """
    key_lower = key.lower()
    return any(pattern in key_lower for pattern in SENSITIVE_KEYS)


def mask_value(value: str) -> str:
    """
    Mask sensitive values for display.

    Short values (4 chars or fewer) are fully masked. Longer values
    show the first 2 and last 2 characters with '***' in between.

    Args:
        value: The sensitive value to mask

    Returns:
        Masked string suitable for display
    """
    if len(value) <= 4:
        return '***'
    return value[:2] + '***' + value[-2:]

@dataclass
class PortValidationResult:
    """Result of port validation, separating valid from invalid ports."""
    valid_ports: list[int]
    invalid_ports: list[int]


def validate_ports(ports: list[int]) -> PortValidationResult:
    """
    Validate a list of port numbers against the valid range (1-65535).

    Separates ports into valid and invalid lists based on whether they
    fall within the standard TCP/UDP port range.

    Args:
        ports: List of integers representing port numbers

    Returns:
        PortValidationResult with valid_ports and invalid_ports lists
    """
    valid = [p for p in ports if 1 <= p <= 65535]
    invalid = [p for p in ports if p < 1 or p > 65535]
    return PortValidationResult(valid_ports=valid, invalid_ports=invalid)

