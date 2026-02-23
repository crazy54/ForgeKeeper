"""
Property-based tests for environment variable extraction and merging.

# Feature: devcontainer-import, Property 7: Environment Variable Extraction and Merging
# Validates: Requirements 7.1, 7.2, 7.3, 7.4

Uses Hypothesis to generate random user configs and imported configs with env vars,
then verifies that merge_config correctly merges them with user values taking priority,
conflicts generating warnings, and no env vars being lost.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from hypothesis import given, settings, assume
import hypothesis.strategies as st

from config_merger import merge_config
from devcontainer_parser import DevcontainerParser


# --- Strategies ---

# Strategy for env var keys (uppercase alphanumeric + underscore, starting with letter)
env_key_st = st.from_regex(r"[A-Z][A-Z0-9_]{0,19}", fullmatch=True)

# Strategy for env var values (printable strings, no null bytes)
env_value_st = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'), blacklist_characters='\x00'),
    min_size=1,
    max_size=50,
)

# Strategy for env var dictionaries
env_vars_st = st.dictionaries(
    keys=env_key_st,
    values=env_value_st,
    min_size=0,
    max_size=10,
)

# Strategy for language lists
languages_st = st.lists(
    st.sampled_from(['python', 'node', 'go', 'rust', 'java', 'dotnet', 'ruby', 'php']),
    unique=True,
    max_size=5,
)

# Strategy for port lists
ports_st = st.lists(
    st.integers(min_value=1, max_value=65535),
    unique=True,
    max_size=5,
)


@st.composite
def user_config_st(draw):
    """Generate a random user configuration dict."""
    config = {}
    config['env_vars'] = draw(env_vars_st)
    config['languages'] = draw(languages_st)
    config['ports'] = draw(ports_st)
    return config


@st.composite
def imported_config_st(draw):
    """Generate a random imported configuration dict."""
    config = {}
    config['env_vars'] = draw(env_vars_st)
    config['languages'] = draw(languages_st)
    config['ports'] = draw(ports_st)
    return config


@st.composite
def configs_with_overlap_st(draw):
    """Generate user and imported configs that share at least one env var key with different values."""
    shared_key = draw(env_key_st)
    user_value = draw(env_value_st)
    imported_value = draw(env_value_st)
    assume(user_value != imported_value)

    user_extra = draw(env_vars_st)
    imported_extra = draw(env_vars_st)

    user_env = {**user_extra, shared_key: user_value}
    imported_env = {**imported_extra, shared_key: imported_value}

    user_config = {'env_vars': user_env, 'languages': draw(languages_st), 'ports': draw(ports_st)}
    imported_config = {'env_vars': imported_env, 'languages': draw(languages_st), 'ports': draw(ports_st)}

    return user_config, imported_config, shared_key


@st.composite
def devcontainer_with_env_st(draw):
    """Generate a devcontainer.json dict that has remoteEnv."""
    remote_env = draw(st.dictionaries(
        keys=env_key_st,
        values=env_value_st,
        min_size=1,
        max_size=8,
    ))
    config = {"remoteEnv": remote_env}
    return config


# --- Property Tests ---

class TestPropertyEnvExtractionAndMerging:
    """
    Property 7: Environment Variable Extraction and Merging

    **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

    For any devcontainer.json with remoteEnv properties, the parser should extract
    all key-value pairs, and the system should merge them with ForgeKeeper defaults,
    prioritizing devcontainer values when conflicts occur.
    """

    def setup_method(self):
        self.parser = DevcontainerParser()

    # --- Requirement 7.1: Parser extracts all key-value pairs from remoteEnv ---

    @given(config=devcontainer_with_env_st())
    @settings(max_examples=100)
    def test_parser_extracts_all_env_key_value_pairs(self, config):
        """
        # Feature: devcontainer-import, Property 7: Environment Variable Extraction and Merging
        **Validates: Requirements 7.1**

        For any devcontainer.json with remoteEnv, the parser should extract
        every key-value pair present in remoteEnv.
        """
        content = json.dumps(config)
        result = self.parser.parse_content(content)

        assert result.success, f"Parsing failed: {result.errors}"
        expected_env = config["remoteEnv"]
        assert result.config.remote_env == expected_env, (
            f"Extracted env vars don't match input. "
            f"Expected: {expected_env}, Got: {result.config.remote_env}"
        )

    # --- Requirement 7.2: Merge imported env vars with user defaults ---

    @given(user=user_config_st(), imported=imported_config_st())
    @settings(max_examples=100)
    def test_all_imported_env_vars_appear_in_merged_result(self, user, imported):
        """
        # Feature: devcontainer-import, Property 7: Environment Variable Extraction and Merging
        **Validates: Requirements 7.2**

        For any user config and imported config, every imported env var should
        appear in the merged result unless overridden by a user env var.
        """
        merged = merge_config(user, imported)
        merged_env = merged['env_vars']

        for key, value in imported['env_vars'].items():
            assert key in merged_env, (
                f"Imported env var '{key}' missing from merged result"
            )
            # If user also has this key, user value wins
            if key in user['env_vars']:
                assert merged_env[key] == user['env_vars'][key]
            else:
                assert merged_env[key] == value

    @given(user=user_config_st(), imported=imported_config_st())
    @settings(max_examples=100)
    def test_all_user_env_vars_appear_in_merged_result(self, user, imported):
        """
        # Feature: devcontainer-import, Property 7: Environment Variable Extraction and Merging
        **Validates: Requirements 7.2**

        For any user config and imported config, every user env var should
        always appear in the merged result with the user's value.
        """
        merged = merge_config(user, imported)
        merged_env = merged['env_vars']

        for key, value in user['env_vars'].items():
            assert key in merged_env, (
                f"User env var '{key}' missing from merged result"
            )
            assert merged_env[key] == value, (
                f"User env var '{key}' has wrong value. "
                f"Expected: '{value}', Got: '{merged_env[key]}'"
            )

    # --- Requirement 7.3: User values take priority on conflicts ---

    @given(data=configs_with_overlap_st())
    @settings(max_examples=100)
    def test_user_env_vars_take_priority_over_imported(self, data):
        """
        # Feature: devcontainer-import, Property 7: Environment Variable Extraction and Merging
        **Validates: Requirements 7.3**

        When user and imported configs have the same env var key with different
        values, the user value must take priority in the merged result.
        """
        user_config, imported_config, shared_key = data
        merged = merge_config(user_config, imported_config)
        merged_env = merged['env_vars']

        assert merged_env[shared_key] == user_config['env_vars'][shared_key], (
            f"User value not prioritized for conflicting key '{shared_key}'. "
            f"Expected: '{user_config['env_vars'][shared_key]}', "
            f"Got: '{merged_env[shared_key]}'"
        )

    @given(data=configs_with_overlap_st())
    @settings(max_examples=100)
    def test_conflicts_generate_warnings(self, data):
        """
        # Feature: devcontainer-import, Property 7: Environment Variable Extraction and Merging
        **Validates: Requirements 7.3**

        When user and imported configs have conflicting env var values,
        the merge should produce a warning mentioning the conflicting key.
        """
        user_config, imported_config, shared_key = data
        merged = merge_config(user_config, imported_config)
        warnings = merged.get('warnings', [])

        conflict_warned = any(shared_key in w for w in warnings)
        assert conflict_warned, (
            f"No warning generated for conflicting key '{shared_key}'. "
            f"Warnings: {warnings}"
        )

    # --- Requirement 7.4: No env vars are lost ---

    @given(user=user_config_st(), imported=imported_config_st())
    @settings(max_examples=100)
    def test_no_env_vars_are_lost_during_merge(self, user, imported):
        """
        # Feature: devcontainer-import, Property 7: Environment Variable Extraction and Merging
        **Validates: Requirements 7.4**

        For any user config and imported config, the union of all env var keys
        from both configs must be present in the merged result.
        """
        merged = merge_config(user, imported)
        merged_env = merged['env_vars']

        all_keys = set(user['env_vars'].keys()) | set(imported['env_vars'].keys())
        merged_keys = set(merged_env.keys())

        assert all_keys == merged_keys, (
            f"Env var keys lost during merge. "
            f"Missing: {all_keys - merged_keys}, "
            f"Extra: {merged_keys - all_keys}"
        )

    @given(user=user_config_st(), imported=imported_config_st())
    @settings(max_examples=100)
    def test_merged_env_var_count_equals_union(self, user, imported):
        """
        # Feature: devcontainer-import, Property 7: Environment Variable Extraction and Merging
        **Validates: Requirements 7.2, 7.4**

        The number of env vars in the merged result should equal the number
        of unique keys across both user and imported configs.
        """
        merged = merge_config(user, imported)
        merged_env = merged['env_vars']

        expected_count = len(set(user['env_vars'].keys()) | set(imported['env_vars'].keys()))
        assert len(merged_env) == expected_count, (
            f"Merged env var count mismatch. "
            f"Expected: {expected_count}, Got: {len(merged_env)}"
        )

    # --- End-to-end: extraction then merging ---

    @given(
        devcontainer=devcontainer_with_env_st(),
        user=user_config_st(),
    )
    @settings(max_examples=100)
    def test_end_to_end_extraction_then_merge(self, devcontainer, user):
        """
        # Feature: devcontainer-import, Property 7: Environment Variable Extraction and Merging
        **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

        For any devcontainer.json with remoteEnv, parsing should extract env vars,
        and merging with a user config should produce a correct result with user
        priority, no lost vars, and appropriate warnings.
        """
        # Step 1: Parse
        content = json.dumps(devcontainer)
        result = self.parser.parse_content(content)
        assert result.success

        # Step 2: Build imported config from parsed result
        imported_config = {'env_vars': result.config.remote_env}

        # Step 3: Merge
        merged = merge_config(user, imported_config)
        merged_env = merged['env_vars']

        # All extracted env vars present (unless overridden)
        for key, value in result.config.remote_env.items():
            assert key in merged_env
            if key in user['env_vars']:
                assert merged_env[key] == user['env_vars'][key]
            else:
                assert merged_env[key] == value

        # All user env vars present
        for key, value in user['env_vars'].items():
            assert key in merged_env
            assert merged_env[key] == value

        # No vars lost
        all_keys = set(user['env_vars'].keys()) | set(result.config.remote_env.keys())
        assert set(merged_env.keys()) == all_keys
