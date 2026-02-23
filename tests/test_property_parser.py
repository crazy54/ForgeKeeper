"""
Property-based tests for DevcontainerParser.

# Feature: devcontainer-import, Property 1: Complete Configuration Extraction
# Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6

Uses Hypothesis to generate valid devcontainer.json structures and verify
that all properties are correctly extracted into the DevcontainerConfig dataclass.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from hypothesis import given, settings, assume
import hypothesis.strategies as st

from devcontainer_parser import DevcontainerParser, DevcontainerConfig


# --- Strategies ---

# Known devcontainer feature IDs for realistic generation
KNOWN_FEATURES = [
    "ghcr.io/devcontainers/features/python:1",
    "ghcr.io/devcontainers/features/node:1",
    "ghcr.io/devcontainers/features/go:1",
    "ghcr.io/devcontainers/features/rust:1",
    "ghcr.io/devcontainers/features/java:1",
    "ghcr.io/devcontainers/features/dotnet:2",
    "ghcr.io/devcontainers/features/ruby:1",
    "ghcr.io/devcontainers/features/php:1",
    "ghcr.io/devcontainers/features/docker-in-docker:2",
    "ghcr.io/devcontainers/features/git:1",
    "ghcr.io/devcontainers/features/common-utils:2",
]

KNOWN_IMAGES = [
    "mcr.microsoft.com/devcontainers/base:ubuntu",
    "mcr.microsoft.com/devcontainers/python:3.11",
    "node:20-bullseye",
    "golang:1.21",
    "rust:1.75",
    "ubuntu:22.04",
]

# Strategy for feature option values
feature_options_st = st.fixed_dictionaries({}, optional={
    "version": st.text(alphabet="0123456789.", min_size=1, max_size=10),
})

# Strategy for features dict
features_st = st.dictionaries(
    keys=st.sampled_from(KNOWN_FEATURES),
    values=feature_options_st,
    min_size=0,
    max_size=5,
)

# Strategy for VS Code extensions
extensions_st = st.lists(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz.-", min_size=3, max_size=30),
    max_size=5,
)

# Strategy for customizations
customizations_st = st.one_of(
    st.just({}),
    st.fixed_dictionaries({
        "vscode": st.fixed_dictionaries({}, optional={
            "extensions": extensions_st,
            "settings": st.dictionaries(
                keys=st.text(alphabet="abcdefghijklmnopqrstuvwxyz.", min_size=1, max_size=20),
                values=st.one_of(st.text(max_size=20), st.booleans(), st.integers(min_value=0, max_value=100)),
                max_size=3,
            ),
        }),
    }),
)

# Strategy for valid port numbers
valid_ports_st = st.lists(
    st.integers(min_value=1, max_value=65535),
    max_size=5,
)

# Strategy for env var keys (alphanumeric + underscore, starting with letter)
env_key_st = st.from_regex(r"[A-Z][A-Z0-9_]{0,19}", fullmatch=True)

# Strategy for env var values
env_value_st = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'), blacklist_characters='\x00'),
    min_size=0,
    max_size=50,
)

# Strategy for remoteEnv
remote_env_st = st.dictionaries(
    keys=env_key_st,
    values=env_value_st,
    max_size=5,
)

# Strategy for image
image_st = st.one_of(st.none(), st.sampled_from(KNOWN_IMAGES))

# Strategy for dockerfile
dockerfile_st = st.one_of(st.none(), st.just("Dockerfile"), st.just("Dockerfile.dev"))


@st.composite
def valid_devcontainer_st(draw):
    """Generate a valid devcontainer.json structure as a dict."""
    features = draw(features_st)
    customizations = draw(customizations_st)
    forward_ports = draw(valid_ports_st)
    remote_env = draw(remote_env_st)
    image = draw(image_st)
    dockerfile = draw(dockerfile_st)

    config = {}

    if features:
        config["features"] = features
    if customizations:
        config["customizations"] = customizations
    if forward_ports:
        config["forwardPorts"] = forward_ports
    if remote_env:
        config["remoteEnv"] = remote_env
    if image is not None:
        config["image"] = image
    if dockerfile is not None:
        config["dockerfile"] = dockerfile

    return config



# --- Property Tests ---

class TestPropertyCompleteExtraction:
    """
    Property 1: Complete Configuration Extraction

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

    For any valid devcontainer.json file, parsing should extract all standard
    properties (features, customizations, forwardPorts, remoteEnv, image/dockerfile)
    and return them in a structured configuration object.
    """

    def setup_method(self):
        self.parser = DevcontainerParser()

    @given(config=valid_devcontainer_st())
    @settings(max_examples=100)
    def test_parsing_always_succeeds_for_valid_input(self, config):
        """
        # Feature: devcontainer-import, Property 1: Complete Configuration Extraction
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

        For any valid devcontainer.json, parsing should succeed and return
        a structured DevcontainerConfig object.
        """
        content = json.dumps(config)
        result = self.parser.parse_content(content)

        assert result.success, f"Parsing failed for valid config: {result.errors}"
        assert result.config is not None
        assert isinstance(result.config, DevcontainerConfig)
        assert result.errors == []

    @given(config=valid_devcontainer_st())
    @settings(max_examples=100)
    def test_features_extracted_correctly(self, config):
        """
        # Feature: devcontainer-import, Property 1: Complete Configuration Extraction
        **Validates: Requirements 2.1**

        For any valid devcontainer.json, the features property should be
        extracted and match the input.
        """
        content = json.dumps(config)
        result = self.parser.parse_content(content)

        assert result.success
        expected_features = config.get("features", {})
        assert result.config.features == expected_features

    @given(config=valid_devcontainer_st())
    @settings(max_examples=100)
    def test_customizations_extracted_correctly(self, config):
        """
        # Feature: devcontainer-import, Property 1: Complete Configuration Extraction
        **Validates: Requirements 2.2**

        For any valid devcontainer.json, the customizations property should be
        extracted and match the input.
        """
        content = json.dumps(config)
        result = self.parser.parse_content(content)

        assert result.success
        expected_customizations = config.get("customizations", {})
        assert result.config.customizations == expected_customizations

    @given(config=valid_devcontainer_st())
    @settings(max_examples=100)
    def test_forward_ports_extracted_correctly(self, config):
        """
        # Feature: devcontainer-import, Property 1: Complete Configuration Extraction
        **Validates: Requirements 2.3**

        For any valid devcontainer.json, the forwardPorts property should be
        extracted and match the input.
        """
        content = json.dumps(config)
        result = self.parser.parse_content(content)

        assert result.success
        expected_ports = config.get("forwardPorts", [])
        assert result.config.forward_ports == expected_ports

    @given(config=valid_devcontainer_st())
    @settings(max_examples=100)
    def test_remote_env_extracted_correctly(self, config):
        """
        # Feature: devcontainer-import, Property 1: Complete Configuration Extraction
        **Validates: Requirements 2.4**

        For any valid devcontainer.json, the remoteEnv property should be
        extracted and match the input.
        """
        content = json.dumps(config)
        result = self.parser.parse_content(content)

        assert result.success
        expected_env = config.get("remoteEnv", {})
        assert result.config.remote_env == expected_env

    @given(config=valid_devcontainer_st())
    @settings(max_examples=100)
    def test_image_config_extracted_correctly(self, config):
        """
        # Feature: devcontainer-import, Property 1: Complete Configuration Extraction
        **Validates: Requirements 2.5**

        For any valid devcontainer.json, the image and dockerfile properties
        should be extracted and match the input.
        """
        content = json.dumps(config)
        result = self.parser.parse_content(content)

        assert result.success
        expected_image = config.get("image")
        expected_dockerfile = config.get("dockerfile")
        assert result.config.image == expected_image
        assert result.config.dockerfile == expected_dockerfile

    @given(config=valid_devcontainer_st())
    @settings(max_examples=100)
    def test_raw_data_preserved(self, config):
        """
        # Feature: devcontainer-import, Property 1: Complete Configuration Extraction
        **Validates: Requirements 2.6**

        For any valid devcontainer.json, the raw data should be preserved
        in the structured configuration object.
        """
        content = json.dumps(config)
        result = self.parser.parse_content(content)

        assert result.success
        assert result.config.raw == config

    @given(config=valid_devcontainer_st())
    @settings(max_examples=100)
    def test_all_fields_have_correct_types(self, config):
        """
        # Feature: devcontainer-import, Property 1: Complete Configuration Extraction
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

        For any valid devcontainer.json, all extracted fields should have
        the correct types in the DevcontainerConfig dataclass.
        """
        content = json.dumps(config)
        result = self.parser.parse_content(content)

        assert result.success
        cfg = result.config
        assert isinstance(cfg.features, dict)
        assert isinstance(cfg.customizations, dict)
        assert isinstance(cfg.forward_ports, list)
        assert all(isinstance(p, int) for p in cfg.forward_ports)
        assert isinstance(cfg.remote_env, dict)
        assert all(isinstance(k, str) and isinstance(v, str) for k, v in cfg.remote_env.items())
        assert cfg.image is None or isinstance(cfg.image, str)
        assert cfg.dockerfile is None or isinstance(cfg.dockerfile, str)
        assert isinstance(cfg.raw, dict)


# --- Strategies for Property 2 ---

# Properties that have specific type constraints in the schema
TYPED_PROPERTIES = {
    "features": "object",
    "customizations": "object",
    "forwardPorts": "array",
    "remoteEnv": "object",
    "image": "string",
    "dockerfile": "string",
    "name": "string",
    "remoteUser": "string",
    "overrideCommand": "boolean",
    "updateRemoteUserUID": "boolean",
    "workspaceFolder": "string",
}

# Strategy to generate a value of the WRONG type for a given expected type
def wrong_type_for(expected_type: str) -> st.SearchStrategy:
    """Generate a value that does NOT match the expected JSON schema type."""
    wrong = {
        "object": st.one_of(
            st.integers(),
            st.text(min_size=1, max_size=10),
            st.lists(st.integers(), min_size=1, max_size=3),
            st.booleans(),
        ),
        "array": st.one_of(
            st.integers(),
            st.text(min_size=1, max_size=10),
            st.dictionaries(keys=st.text(min_size=1, max_size=5), values=st.integers(), min_size=1, max_size=2),
            st.booleans(),
        ),
        "string": st.one_of(
            st.integers(),
            st.lists(st.integers(), min_size=1, max_size=3),
            st.booleans(),
            st.dictionaries(keys=st.text(min_size=1, max_size=5), values=st.integers(), min_size=1, max_size=2),
        ),
        "boolean": st.one_of(
            st.integers(),
            st.text(min_size=1, max_size=10),
            st.lists(st.integers(), min_size=1, max_size=3),
        ),
    }
    return wrong[expected_type]


@st.composite
def invalid_typed_devcontainer_st(draw):
    """Generate a devcontainer.json dict with at least one property having the wrong type."""
    prop_name = draw(st.sampled_from(list(TYPED_PROPERTIES.keys())))
    expected_type = TYPED_PROPERTIES[prop_name]
    bad_value = draw(wrong_type_for(expected_type))
    return {prop_name: bad_value}, prop_name


# Strategy for generating invalid JSON strings
@st.composite
def invalid_json_st(draw):
    """Generate strings that are not valid JSON."""
    choice = draw(st.sampled_from([
        "truncated_brace",
        "trailing_comma",
        "unquoted_key",
        "single_quotes",
        "random_text",
        "missing_colon",
    ]))
    if choice == "truncated_brace":
        return '{"name": "test"'
    elif choice == "trailing_comma":
        return '{"name": "test",}'
    elif choice == "unquoted_key":
        return '{name: "test"}'
    elif choice == "single_quotes":
        return "{'name': 'test'}"
    elif choice == "random_text":
        text = draw(st.text(
            alphabet=st.characters(whitelist_categories=('L', 'N', 'P')),
            min_size=1,
            max_size=50,
        ))
        assume(not _is_valid_json_object(text))
        return text
    else:  # missing_colon
        return '{"name" "test"}'


def _is_valid_json_object(s: str) -> bool:
    """Check if a string is valid JSON that parses to a dict."""
    try:
        result = json.loads(s)
        return isinstance(result, dict)
    except (json.JSONDecodeError, ValueError):
        return False


# --- Property 2 Tests ---

class TestPropertySchemaValidation:
    """
    Property 2: Schema Validation Correctness

    **Validates: Requirements 1.4, 1.5**

    For any JSON input, the parser should correctly identify whether it conforms
    to the devcontainer.json schema, accepting valid configurations and rejecting
    invalid ones with descriptive errors.
    """
    # Feature: devcontainer-import, Property 2: Schema Validation Correctness

    def setup_method(self):
        self.parser = DevcontainerParser()

    @given(config=valid_devcontainer_st())
    @settings(max_examples=100)
    def test_valid_configs_pass_schema_validation(self, config):
        """
        # Feature: devcontainer-import, Property 2: Schema Validation Correctness
        **Validates: Requirements 1.4**

        For any valid devcontainer.json structure, the parser should accept it
        and return a successful result with no errors.
        """
        content = json.dumps(config)
        result = self.parser.parse_content(content)

        assert result.success, f"Valid config rejected: {result.errors}"
        assert result.config is not None
        assert result.errors == []

    @given(data=invalid_typed_devcontainer_st())
    @settings(max_examples=100)
    def test_invalid_types_fail_with_descriptive_errors(self, data):
        """
        # Feature: devcontainer-import, Property 2: Schema Validation Correctness
        **Validates: Requirements 1.4, 1.5**

        For any devcontainer.json with a property of the wrong type,
        the parser should reject it and return descriptive error messages.
        """
        config_dict, bad_prop = data
        content = json.dumps(config_dict)
        result = self.parser.parse_content(content)

        assert not result.success, (
            f"Invalid config accepted: property '{bad_prop}' had wrong type "
            f"but parsing succeeded"
        )
        assert len(result.errors) > 0, "Expected at least one error message"
        # Errors should be descriptive (non-empty strings with meaningful content)
        for error in result.errors:
            assert isinstance(error, str)
            assert len(error) > 10, f"Error message too short to be descriptive: '{error}'"

    @given(bad_json=invalid_json_st())
    @settings(max_examples=100)
    def test_invalid_json_produces_descriptive_parse_errors(self, bad_json):
        """
        # Feature: devcontainer-import, Property 2: Schema Validation Correctness
        **Validates: Requirements 1.5**

        For any invalid JSON string, the parser should reject it and return
        a descriptive error message indicating the parse failure.
        """
        result = self.parser.parse_content(bad_json)

        assert not result.success, f"Invalid JSON accepted: '{bad_json[:50]}'"
        assert len(result.errors) > 0, "Expected at least one error message"
        for error in result.errors:
            assert isinstance(error, str)
            assert len(error) > 10, f"Error message too short to be descriptive: '{error}'"

    @given(config=valid_devcontainer_st())
    @settings(max_examples=100)
    def test_validate_schema_returns_empty_for_valid(self, config):
        """
        # Feature: devcontainer-import, Property 2: Schema Validation Correctness
        **Validates: Requirements 1.4**

        For any valid devcontainer.json dict, validate_schema should return
        an empty list of errors.
        """
        errors = self.parser.validate_schema(config)
        assert errors == [], f"validate_schema returned errors for valid config: {errors}"

    @given(data=invalid_typed_devcontainer_st())
    @settings(max_examples=100)
    def test_validate_schema_returns_errors_for_invalid(self, data):
        """
        # Feature: devcontainer-import, Property 2: Schema Validation Correctness
        **Validates: Requirements 1.4, 1.5**

        For any devcontainer.json dict with wrong-typed properties,
        validate_schema should return a non-empty list of descriptive errors.
        """
        config_dict, bad_prop = data
        errors = self.parser.validate_schema(config_dict)

        assert len(errors) > 0, (
            f"validate_schema returned no errors for invalid config "
            f"(property '{bad_prop}' had wrong type)"
        )
        for error in errors:
            assert isinstance(error, str)
            assert len(error) > 0

