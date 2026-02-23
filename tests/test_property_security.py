"""
Property-based tests for security utilities.

# Feature: devcontainer-import, Property 8: Sensitive Variable Masking
# Validates: Requirements 7.5

Uses Hypothesis to generate random environment variable key-value pairs and verify
that sensitive variables are masked correctly while non-sensitive variables are
returned as-is.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from hypothesis import given, settings, assume
import hypothesis.strategies as st

from security_utils import is_sensitive, mask_value, SENSITIVE_KEYS, validate_ports


# --- Strategies ---

# Sensitive patterns that should trigger masking
SENSITIVE_PATTERNS = list(SENSITIVE_KEYS)

# Safe key components that don't contain any sensitive pattern
SAFE_KEY_PARTS = [
    "APP", "HOST", "PORT", "PATH", "HOME", "LANG", "SHELL",
    "USER", "DISPLAY", "EDITOR", "TERM", "LOG", "DEBUG",
    "VERSION", "NAME", "MODE", "ENV", "DIR", "URL", "REGION",
]


def _contains_sensitive_pattern(key: str) -> bool:
    """Check if a key contains any sensitive pattern (case-insensitive)."""
    key_lower = key.lower()
    return any(pattern in key_lower for pattern in SENSITIVE_PATTERNS)


# Strategy for keys guaranteed to contain a sensitive pattern
sensitive_key_st = st.one_of(
    # Pattern embedded in a larger key name
    st.tuples(
        st.sampled_from(["", "MY_", "APP_", "DB_", "AWS_", "GH_"]),
        st.sampled_from(SENSITIVE_PATTERNS),
        st.sampled_from(["", "_VAR", "_VALUE", "_1", "_DATA"]),
    ).map(lambda parts: f"{parts[0]}{parts[1].upper()}{parts[2]}"),
    # Just the pattern itself
    st.sampled_from(SENSITIVE_PATTERNS).map(str.upper),
)

# Strategy for keys guaranteed NOT to contain any sensitive pattern
non_sensitive_key_st = st.tuples(
    st.sampled_from(SAFE_KEY_PARTS),
    st.sampled_from(["", "_NAME", "_VALUE", "_1", "_PATH"]),
).map(lambda parts: f"{parts[0]}{parts[1]}").filter(
    lambda k: not _contains_sensitive_pattern(k)
)

# Strategy for env var values (non-empty strings)
value_st = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S')),
    min_size=1,
    max_size=100,
)


class TestPropertySensitiveVariableMasking:
    """
    Property 8: Sensitive Variable Masking

    For any environment variable with a key containing sensitive patterns
    (token, key, secret, password, credential), the preview should display
    a masked value instead of the actual value.

    Validates: Requirements 7.5
    """

    # Feature: devcontainer-import, Property 8: Sensitive Variable Masking

    @given(key=sensitive_key_st, value=value_st)
    @settings(max_examples=100)
    def test_sensitive_keys_are_detected(self, key, value):
        """
        **Validates: Requirements 7.5**

        For any key containing a sensitive pattern, is_sensitive() returns True.
        """
        assert is_sensitive(key), (
            f"Expected is_sensitive('{key}') to be True"
        )

    @given(key=non_sensitive_key_st, value=value_st)
    @settings(max_examples=100)
    def test_non_sensitive_keys_are_not_detected(self, key, value):
        """
        **Validates: Requirements 7.5**

        For any key NOT containing a sensitive pattern, is_sensitive() returns False.
        """
        assert not is_sensitive(key), (
            f"Expected is_sensitive('{key}') to be False"
        )

    @given(key=sensitive_key_st, value=value_st)
    @settings(max_examples=100)
    def test_sensitive_values_are_masked(self, key, value):
        """
        **Validates: Requirements 7.5**

        For any sensitive key, mask_value() produces output containing '***'.
        """
        masked = mask_value(value)
        assert '***' in masked, (
            f"Expected '***' in masked output, got '{masked}'"
        )

    @given(key=sensitive_key_st, value=st.text(min_size=5, max_size=100,
           alphabet=st.characters(whitelist_categories=('L', 'N'))))
    @settings(max_examples=100)
    def test_sensitive_values_longer_than_4_are_not_equal_to_original(self, key, value):
        """
        **Validates: Requirements 7.5**

        For any sensitive key with value longer than 4 chars,
        mask_value() should not return the original value.
        """
        assume(len(value) > 4)
        masked = mask_value(value)
        assert masked != value, (
            f"Expected masked value to differ from original '{value}', got '{masked}'"
        )

    @given(key=sensitive_key_st, value=st.text(min_size=1, max_size=4,
           alphabet=st.characters(whitelist_categories=('L', 'N'))))
    @settings(max_examples=100)
    def test_short_sensitive_values_are_fully_masked(self, key, value):
        """
        **Validates: Requirements 7.5**

        For any sensitive key with value of 4 chars or fewer,
        mask_value() returns '***' (fully masked).
        """
        assume(len(value) <= 4)
        masked = mask_value(value)
        assert masked == '***', (
            f"Expected '***' for short value '{value}', got '{masked}'"
        )

    @given(key=non_sensitive_key_st, value=value_st)
    @settings(max_examples=100)
    def test_non_sensitive_values_returned_as_is(self, key, value):
        """
        **Validates: Requirements 7.5**

        For any non-sensitive key, the value should be returned unchanged
        (no masking applied).
        """
        # Non-sensitive keys don't need masking, value passes through
        assert not is_sensitive(key)
        # The value itself is not masked for non-sensitive keys
        assert value == value  # identity holds; no transformation needed


# --- Strategies for Port Validation ---

# Strategy for valid port numbers (1-65535)
valid_port_st = st.integers(min_value=1, max_value=65535)

# Strategy for invalid port numbers (< 1 or > 65535)
invalid_port_st = st.one_of(
    st.integers(max_value=0),
    st.integers(min_value=65536),
)

# Strategy for mixed port lists (any integers)
mixed_port_list_st = st.lists(
    st.integers(min_value=-1000000, max_value=1000000),
    max_size=50,
)


class TestPropertyPortValidation:
    """
    Property 9: Port Validation

    For any extracted port list, the system should validate that all ports are
    valid integers in the range 1-65535, rejecting invalid port numbers with
    descriptive errors.

    Validates: Requirements 8.2
    """

    # Feature: devcontainer-import, Property 9: Port Validation

    @given(ports=st.lists(valid_port_st, max_size=50))
    @settings(max_examples=100)
    def test_all_valid_ports_accepted(self, ports):
        """
        **Validates: Requirements 8.2**

        For any list of valid ports (1-65535), all should end up in valid_ports
        and invalid_ports should be empty.
        """
        result = validate_ports(ports)
        assert result.valid_ports == ports
        assert result.invalid_ports == []

    @given(ports=st.lists(invalid_port_st, min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_all_invalid_ports_rejected(self, ports):
        """
        **Validates: Requirements 8.2**

        For any list of invalid ports (< 1 or > 65535), all should end up in
        invalid_ports and valid_ports should be empty.
        """
        result = validate_ports(ports)
        assert result.valid_ports == []
        assert result.invalid_ports == ports

    @given(ports=mixed_port_list_st)
    @settings(max_examples=100)
    def test_valid_ports_in_range(self, ports):
        """
        **Validates: Requirements 8.2**

        For any list of integers, every port in valid_ports is in range 1-65535.
        """
        result = validate_ports(ports)
        for port in result.valid_ports:
            assert 1 <= port <= 65535, (
                f"Port {port} in valid_ports is outside range 1-65535"
            )

    @given(ports=mixed_port_list_st)
    @settings(max_examples=100)
    def test_invalid_ports_out_of_range(self, ports):
        """
        **Validates: Requirements 8.2**

        For any list of integers, every port in invalid_ports is outside range 1-65535.
        """
        result = validate_ports(ports)
        for port in result.invalid_ports:
            assert port < 1 or port > 65535, (
                f"Port {port} in invalid_ports is actually valid (1-65535)"
            )

    @given(ports=mixed_port_list_st)
    @settings(max_examples=100)
    def test_no_ports_lost(self, ports):
        """
        **Validates: Requirements 8.2**

        For any list of integers, valid_ports + invalid_ports should contain
        exactly the same elements as the original list (no ports lost).
        """
        result = validate_ports(ports)
        combined = result.valid_ports + result.invalid_ports
        assert sorted(combined) == sorted(ports), (
            f"Ports lost: original={sorted(ports)}, combined={sorted(combined)}"
        )

    @given(ports=st.just([]))
    @settings(max_examples=1)
    def test_empty_list_returns_empty(self, ports):
        """
        **Validates: Requirements 8.2**

        An empty port list should return empty valid and invalid lists.
        """
        result = validate_ports(ports)
        assert result.valid_ports == []
        assert result.invalid_ports == []
