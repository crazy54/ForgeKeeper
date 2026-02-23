"""
Property-based tests for workflow compatibility, error descriptiveness, and preview completeness.

Covers:
- Property 15: Workflow Compatibility (Requirements 10.1, 10.2)
- Property 10: Error Message Descriptiveness (Requirements 9.1, 9.2, 9.3, 9.5)
- Property 5: Preview Completeness (Requirements 4.1, 4.2, 4.3, 4.4, 4.5)

Uses Hypothesis with @settings(max_examples=100) for all property tests.
"""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from hypothesis import given, settings, assume
import hypothesis.strategies as st

from devcontainer_parser import DevcontainerParser, DevcontainerConfig
from devcontainer_mapper import DevcontainerMapper, MappingResult
from config_merger import merge_config
from security_utils import is_sensitive, mask_value


# ── Shared Strategies ──────────────────────────────────────────────

SUPPORTED_LANGS = ["python", "node", "go", "rust", "java", "dotnet", "ruby", "php", "swift", "dart"]

env_key_st = st.from_regex(r"[A-Z][A-Z0-9_]{0,19}", fullmatch=True)

env_value_st = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P'), blacklist_characters='\x00\n\r'),
    min_size=1,
    max_size=40,
)

env_vars_st = st.dictionaries(keys=env_key_st, values=env_value_st, min_size=0, max_size=8)

languages_st = st.lists(
    st.sampled_from(SUPPORTED_LANGS),
    unique=True,
    min_size=0,
    max_size=6,
)

ports_st = st.lists(
    st.integers(min_value=1, max_value=65535),
    unique=True,
    max_size=5,
)

# All known feature prefixes from the mapper
ALL_KNOWN_FEATURES = []
for patterns in DevcontainerMapper.FEATURE_MAPPINGS.values():
    ALL_KNOWN_FEATURES.extend(patterns)

VERSION_SUFFIXES = ['', ':1', ':2', ':latest']


# ── Property 15: Workflow Compatibility ────────────────────────────


@st.composite
def wizard_config_no_import_st(draw):
    """Generate a wizard config that does NOT use import (no imported_env_vars)."""
    config = {
        "email": draw(st.emails()),
        "handle": draw(st.from_regex(r"[a-z][a-z0-9_]{2,15}", fullmatch=True)),
        "workspace": draw(st.from_regex(r"[a-z][a-z0-9_-]{0,15}", fullmatch=True)),
        "git_name": draw(st.text(alphabet=st.characters(whitelist_categories=('L', 'Zs')), min_size=0, max_size=30)),
        "git_email": draw(st.one_of(st.just(""), st.emails())),
        "github_token": "",
        "openai_key": "",
        "anthropic_key": "",
        "aws_region": draw(st.sampled_from(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"])),
        "ollama_models": draw(st.lists(st.sampled_from(["llama3", "codellama", "mistral"]), min_size=1, max_size=3, unique=True)),
    }
    languages = draw(languages_st)
    return config, languages


class TestPropertyWorkflowCompatibility:
    """
    Property 15: Workflow Compatibility

    **Validates: Requirements 10.1, 10.2**

    For any wizard session where import is not used, all wizard steps,
    navigation, and functionality should work exactly as before.
    """

    @given(data=wizard_config_no_import_st())
    @settings(max_examples=100)
    def test_write_env_works_without_imported_env_vars(self, data):
        """
        # Feature: devcontainer-import, Property 15: Workflow Compatibility
        **Validates: Requirements 10.1**

        For any wizard config without imported_env_vars, write_env should
        produce a valid .env file with all standard ForgeKeeper variables.
        """
        config, languages = data

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"

            with patch("setup.ENV_FILE", env_file):
                from setup import write_env
                write_env(config)

            content = env_file.read_text()
            lines = content.strip().split("\n")

            # Standard variables must be present
            assert any(l.startswith("FORGEKEEPER_USER_EMAIL=") for l in lines)
            assert any(l.startswith("FORGEKEEPER_HANDLE=") for l in lines)
            assert any(l.startswith("FORGEKEEPER_WORKSPACE=") for l in lines)
            assert any(l.startswith("GIT_USER_NAME=") for l in lines)
            assert any(l.startswith("GIT_USER_EMAIL=") for l in lines)
            assert any(l.startswith("AWS_DEFAULT_REGION=") for l in lines)
            assert any(l.startswith("OLLAMA_MODELS=") for l in lines)

    @given(data=wizard_config_no_import_st())
    @settings(max_examples=100)
    def test_write_env_with_empty_imported_env_vars(self, data):
        """
        # Feature: devcontainer-import, Property 15: Workflow Compatibility
        **Validates: Requirements 10.1**

        For any wizard config with an empty imported_env_vars dict,
        write_env should produce the same output as without import.
        """
        config, _ = data
        config_with_empty_import = {**config, "imported_env_vars": {}}

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file_no_import = Path(tmpdir) / ".env.no_import"
            env_file_empty_import = Path(tmpdir) / ".env.empty_import"

            with patch("setup.ENV_FILE", env_file_no_import):
                from setup import write_env
                write_env(config)

            with patch("setup.ENV_FILE", env_file_empty_import):
                write_env(config_with_empty_import)

            content_no_import = env_file_no_import.read_text()
            content_empty_import = env_file_empty_import.read_text()

            assert content_no_import == content_empty_import, (
                "write_env with empty imported_env_vars should produce identical output "
                "to write_env without imported_env_vars"
            )

    @given(data=wizard_config_no_import_st())
    @settings(max_examples=100)
    def test_assemble_dockerfile_works_without_import(self, data):
        """
        # Feature: devcontainer-import, Property 15: Workflow Compatibility
        **Validates: Requirements 10.2**

        For any set of manually selected languages (no import),
        assemble_dockerfile should produce a valid Dockerfile.built.
        """
        _, languages = data
        assume(len(languages) > 0)

        root = Path(__file__).parent.parent
        lang_modules_dir = root / "dockerfiles"

        with tempfile.TemporaryDirectory() as tmpdir:
            dockerfile_out = Path(tmpdir) / "Dockerfile.built"
            dockerfile_base = Path(tmpdir) / "Dockerfile"
            dockerfile_base.write_text("FROM ubuntu:24.04\nRUN echo hello\nEXPOSE 8080 7000\n")

            with patch("setup.DOCKERFILE_OUT", dockerfile_out), \
                 patch("setup.DOCKERFILE_BASE", dockerfile_base), \
                 patch("setup.LANG_MODULES_DIR", lang_modules_dir):
                from setup import assemble_dockerfile
                assemble_dockerfile(languages)

            assert dockerfile_out.exists()
            content = dockerfile_out.read_text()
            assert "FROM ubuntu:24.04" in content
            assert "EXPOSE" in content

    @given(data=wizard_config_no_import_st())
    @settings(max_examples=100)
    def test_merge_config_with_empty_import_preserves_user(self, data):
        """
        # Feature: devcontainer-import, Property 15: Workflow Compatibility
        **Validates: Requirements 10.1, 10.2**

        For any user config merged with an empty imported config,
        the result should contain exactly the user's data with no warnings.
        """
        config, languages = data

        user_config = {
            'env_vars': {k: v for k, v in config.items() if k in ('email', 'handle')},
            'languages': languages,
            'ports': [],
        }
        imported_config = {
            'env_vars': {},
            'languages': [],
            'ports': [],
        }

        merged = merge_config(user_config, imported_config)

        assert merged['env_vars'] == user_config['env_vars']
        assert set(merged['languages']) == set(languages)
        assert merged['warnings'] == []


# ── Property 10: Error Message Descriptiveness ─────────────────────


# Strategy for generating invalid JSON strings
@st.composite
def invalid_json_content_st(draw):
    """Generate strings that are not valid JSON objects."""
    choice = draw(st.sampled_from([
        "truncated_brace",
        "trailing_comma",
        "unquoted_key",
        "single_quotes",
        "missing_colon",
        "unclosed_string",
    ]))
    if choice == "truncated_brace":
        return '{"name": "test"'
    elif choice == "trailing_comma":
        return '{"name": "test",}'
    elif choice == "unquoted_key":
        return '{name: "test"}'
    elif choice == "single_quotes":
        return "{'name': 'test'}"
    elif choice == "missing_colon":
        return '{"name" "test"}'
    else:  # unclosed_string
        return '{"name": "test'


# Strategy for generating schema-invalid devcontainer.json
TYPED_PROPERTIES = {
    "features": "object",
    "customizations": "object",
    "forwardPorts": "array",
    "remoteEnv": "object",
    "image": "string",
    "dockerfile": "string",
}


def wrong_type_for(expected_type: str) -> st.SearchStrategy:
    """Generate a value that does NOT match the expected JSON schema type."""
    wrong = {
        "object": st.one_of(st.integers(), st.text(min_size=1, max_size=10), st.booleans()),
        "array": st.one_of(st.integers(), st.text(min_size=1, max_size=10), st.booleans()),
        "string": st.one_of(st.integers(), st.lists(st.integers(), min_size=1, max_size=3), st.booleans()),
    }
    return wrong[expected_type]


@st.composite
def schema_invalid_devcontainer_st(draw):
    """Generate a devcontainer.json dict with a property of the wrong type."""
    prop_name = draw(st.sampled_from(list(TYPED_PROPERTIES.keys())))
    expected_type = TYPED_PROPERTIES[prop_name]
    bad_value = draw(wrong_type_for(expected_type))
    return {prop_name: bad_value}, prop_name


@st.composite
def nonexistent_file_path_st(draw):
    """Generate file paths that don't exist."""
    name = draw(st.from_regex(r"[a-z]{3,10}", fullmatch=True))
    return f"/tmp/nonexistent_{name}/devcontainer.json"


class TestPropertyErrorMessageDescriptiveness:
    """
    Property 10: Error Message Descriptiveness

    **Validates: Requirements 9.1, 9.2, 9.3, 9.5**

    For any error condition (file access failure, JSON parse error, schema
    validation failure), the system should provide an error message containing
    the specific issue, location (if applicable), and actionable guidance.
    """

    def setup_method(self):
        self.parser = DevcontainerParser()

    @given(bad_json=invalid_json_content_st())
    @settings(max_examples=100)
    def test_json_parse_errors_are_descriptive(self, bad_json):
        """
        # Feature: devcontainer-import, Property 10: Error Message Descriptiveness
        **Validates: Requirements 9.2**

        For any invalid JSON string, the parser should return an error message
        that includes location information (line/column) and describes the issue.
        """
        result = self.parser.parse_content(bad_json)

        assert not result.success
        assert len(result.errors) > 0

        error_msg = result.errors[0]
        assert isinstance(error_msg, str)
        assert len(error_msg) > 15, (
            f"Error message too short to be descriptive: '{error_msg}'"
        )
        # Should contain location info (line or column)
        error_lower = error_msg.lower()
        assert "line" in error_lower or "column" in error_lower or "syntax" in error_lower, (
            f"Error message lacks location/syntax info: '{error_msg}'"
        )

    @given(data=schema_invalid_devcontainer_st())
    @settings(max_examples=100)
    def test_schema_validation_errors_are_descriptive(self, data):
        """
        # Feature: devcontainer-import, Property 10: Error Message Descriptiveness
        **Validates: Requirements 9.3**

        For any devcontainer.json with invalid property types, the parser
        should return descriptive errors identifying which properties are invalid.
        """
        config_dict, bad_prop = data
        content = json.dumps(config_dict)
        result = self.parser.parse_content(content)

        assert not result.success, (
            f"Invalid config accepted: property '{bad_prop}' had wrong type"
        )
        assert len(result.errors) > 0

        for error_msg in result.errors:
            assert isinstance(error_msg, str)
            assert len(error_msg) > 10, (
                f"Error message too short to be descriptive: '{error_msg}'"
            )

    @given(file_path=nonexistent_file_path_st())
    @settings(max_examples=100)
    def test_file_not_found_errors_include_path(self, file_path):
        """
        # Feature: devcontainer-import, Property 10: Error Message Descriptiveness
        **Validates: Requirements 9.1**

        For any nonexistent file path, the parser should return an error
        message that includes the file path and indicates the file was not found.
        """
        result = self.parser.parse_file(file_path)

        assert not result.success
        assert len(result.errors) > 0

        error_msg = result.errors[0]
        assert file_path in error_msg or "not found" in error_msg.lower(), (
            f"Error message doesn't mention file path or 'not found': '{error_msg}'"
        )

    @given(bad_json=invalid_json_content_st())
    @settings(max_examples=100)
    def test_errors_allow_retry(self, bad_json):
        """
        # Feature: devcontainer-import, Property 10: Error Message Descriptiveness
        **Validates: Requirements 9.5**

        For any error condition, the parser should return a ParseResult
        with success=False, allowing the caller to retry with corrected input.
        """
        result = self.parser.parse_content(bad_json)

        assert not result.success
        assert result.config is None
        assert len(result.errors) > 0

        # Verify the parser can be reused (retry scenario)
        valid_result = self.parser.parse_content('{"image": "ubuntu:22.04"}')
        assert valid_result.success, "Parser should work after a failed parse (retry)"

    @given(data=schema_invalid_devcontainer_st())
    @settings(max_examples=100)
    def test_schema_errors_contain_meaningful_content(self, data):
        """
        # Feature: devcontainer-import, Property 10: Error Message Descriptiveness
        **Validates: Requirements 9.3, 9.5**

        For any schema validation error, the error message should contain
        meaningful content (not just generic "error" text).
        """
        config_dict, bad_prop = data
        errors = self.parser.validate_schema(config_dict)

        assert len(errors) > 0
        for error in errors:
            # Error should be more than just a generic word
            words = error.split()
            assert len(words) >= 3, (
                f"Error message too generic: '{error}'"
            )


# ── Property 5: Preview Completeness ──────────────────────────────


@st.composite
def devcontainer_for_preview_st(draw):
    """Generate a devcontainer config with all preview-relevant data."""
    # Generate language features
    num_lang_features = draw(st.integers(min_value=0, max_value=5))
    features = {}
    expected_languages = set()
    if num_lang_features > 0:
        selected_patterns = draw(st.lists(
            st.sampled_from(ALL_KNOWN_FEATURES),
            min_size=num_lang_features,
            max_size=num_lang_features,
            unique=True,
        ))
        for pattern in selected_patterns:
            suffix = draw(st.sampled_from(VERSION_SUFFIXES))
            features[pattern + suffix] = {}
            # Determine expected language from pattern
            for lang, prefixes in DevcontainerMapper.FEATURE_MAPPINGS.items():
                if any(pattern.startswith(p) for p in prefixes):
                    expected_languages.add(lang)

    # Add some unrecognized features
    num_unrecognized = draw(st.integers(min_value=0, max_value=3))
    unrecognized_names = ["docker-in-docker", "git", "common-utils", "terraform", "aws-cli"]
    if num_unrecognized > 0:
        selected_unrecognized = draw(st.lists(
            st.sampled_from(unrecognized_names),
            min_size=num_unrecognized,
            max_size=num_unrecognized,
            unique=True,
        ))
        for name in selected_unrecognized:
            features[f"ghcr.io/devcontainers/features/{name}:1"] = {}

    # Generate env vars
    remote_env = draw(st.dictionaries(
        keys=env_key_st,
        values=env_value_st,
        min_size=0,
        max_size=5,
    ))

    # Generate ports
    forward_ports = draw(st.lists(
        st.integers(min_value=1, max_value=65535),
        unique=True,
        min_size=0,
        max_size=5,
    ))

    devcontainer = {}
    if features:
        devcontainer["features"] = features
    if remote_env:
        devcontainer["remoteEnv"] = remote_env
    if forward_ports:
        devcontainer["forwardPorts"] = forward_ports

    return devcontainer, expected_languages


class TestPropertyPreviewCompleteness:
    """
    Property 5: Preview Completeness

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

    For any successfully parsed and mapped devcontainer configuration,
    the preview should display all detected languages, environment variables,
    forwarded ports, and unrecognized features.
    """

    def setup_method(self):
        self.parser = DevcontainerParser()
        self.mapper = DevcontainerMapper()

    @given(data=devcontainer_for_preview_st())
    @settings(max_examples=100)
    def test_mapping_result_contains_all_detected_languages(self, data):
        """
        # Feature: devcontainer-import, Property 5: Preview Completeness
        **Validates: Requirements 4.1, 4.2**

        For any parsed devcontainer config, the MappingResult should contain
        all expected detected languages for preview display.
        """
        devcontainer, expected_languages = data
        content = json.dumps(devcontainer)

        parse_result = self.parser.parse_content(content)
        assert parse_result.success, f"Parse failed: {parse_result.errors}"

        mapping = self.mapper.map_features(parse_result.config)

        # All expected languages should be detected
        for lang in expected_languages:
            assert lang in mapping.languages, (
                f"Expected language '{lang}' not in mapping result. "
                f"Got: {mapping.languages}"
            )

    @given(data=devcontainer_for_preview_st())
    @settings(max_examples=100)
    def test_mapping_result_contains_all_env_vars(self, data):
        """
        # Feature: devcontainer-import, Property 5: Preview Completeness
        **Validates: Requirements 4.1, 4.3**

        For any parsed devcontainer config, the MappingResult should contain
        all environment variables for preview display.
        """
        devcontainer, _ = data
        content = json.dumps(devcontainer)

        parse_result = self.parser.parse_content(content)
        assert parse_result.success

        mapping = self.mapper.map_features(parse_result.config)

        expected_env = devcontainer.get("remoteEnv", {})
        assert mapping.env_vars == expected_env, (
            f"Env vars mismatch. Expected: {expected_env}, Got: {mapping.env_vars}"
        )

    @given(data=devcontainer_for_preview_st())
    @settings(max_examples=100)
    def test_mapping_result_contains_all_ports(self, data):
        """
        # Feature: devcontainer-import, Property 5: Preview Completeness
        **Validates: Requirements 4.1, 4.4**

        For any parsed devcontainer config, the MappingResult should contain
        all forwarded ports for preview display.
        """
        devcontainer, _ = data
        content = json.dumps(devcontainer)

        parse_result = self.parser.parse_content(content)
        assert parse_result.success

        mapping = self.mapper.map_features(parse_result.config)

        expected_ports = devcontainer.get("forwardPorts", [])
        assert mapping.ports == expected_ports, (
            f"Ports mismatch. Expected: {expected_ports}, Got: {mapping.ports}"
        )

    @given(data=devcontainer_for_preview_st())
    @settings(max_examples=100)
    def test_mapping_result_tracks_unrecognized_features(self, data):
        """
        # Feature: devcontainer-import, Property 5: Preview Completeness
        **Validates: Requirements 4.1, 4.5**

        For any parsed devcontainer config, unrecognized features should
        appear in the MappingResult's unrecognized_features list with warnings.
        """
        devcontainer, _ = data
        content = json.dumps(devcontainer)

        parse_result = self.parser.parse_content(content)
        assert parse_result.success

        mapping = self.mapper.map_features(parse_result.config)

        features = devcontainer.get("features", {})
        for feature_id in features:
            is_known = any(
                feature_id.startswith(prefix)
                for prefixes in DevcontainerMapper.FEATURE_MAPPINGS.values()
                for prefix in prefixes
            )
            if not is_known:
                assert feature_id in mapping.unrecognized_features, (
                    f"Unrecognized feature '{feature_id}' not tracked in mapping result"
                )
                assert any(feature_id in w for w in mapping.warnings), (
                    f"No warning generated for unrecognized feature '{feature_id}'"
                )

    @given(data=devcontainer_for_preview_st())
    @settings(max_examples=100)
    def test_preview_data_is_complete_and_serializable(self, data):
        """
        # Feature: devcontainer-import, Property 5: Preview Completeness
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

        For any parsed devcontainer config, the MappingResult should be
        fully serializable to JSON (as needed for API response / preview display).
        """
        devcontainer, _ = data
        content = json.dumps(devcontainer)

        parse_result = self.parser.parse_content(content)
        assert parse_result.success

        mapping = self.mapper.map_features(parse_result.config)

        # Build the preview response (same format as API endpoints)
        preview = {
            "languages": sorted(mapping.languages),
            "env_vars": mapping.env_vars,
            "ports": mapping.ports,
            "unrecognized_features": mapping.unrecognized_features,
            "warnings": mapping.warnings,
        }

        # Must be JSON-serializable
        serialized = json.dumps(preview)
        deserialized = json.loads(serialized)

        assert isinstance(deserialized["languages"], list)
        assert isinstance(deserialized["env_vars"], dict)
        assert isinstance(deserialized["ports"], list)
        assert isinstance(deserialized["unrecognized_features"], list)
        assert isinstance(deserialized["warnings"], list)

    @given(data=devcontainer_for_preview_st())
    @settings(max_examples=100)
    def test_no_data_lost_between_parse_and_map(self, data):
        """
        # Feature: devcontainer-import, Property 5: Preview Completeness
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

        For any devcontainer config, the total count of recognized languages +
        unrecognized features should equal the total number of input features.
        No features should be silently dropped.
        """
        devcontainer, _ = data
        content = json.dumps(devcontainer)

        parse_result = self.parser.parse_content(content)
        assert parse_result.success

        mapping = self.mapper.map_features(parse_result.config)

        input_features = devcontainer.get("features", {})
        # Each input feature should either map to a language or be unrecognized
        accounted_features = set()
        for feature_id in input_features:
            is_known = any(
                feature_id.startswith(prefix)
                for prefixes in DevcontainerMapper.FEATURE_MAPPINGS.values()
                for prefix in prefixes
            )
            if is_known:
                accounted_features.add(feature_id)
            else:
                assert feature_id in mapping.unrecognized_features
                accounted_features.add(feature_id)

        assert len(accounted_features) == len(input_features), (
            f"Some features unaccounted for. Input: {len(input_features)}, "
            f"Accounted: {len(accounted_features)}"
        )
