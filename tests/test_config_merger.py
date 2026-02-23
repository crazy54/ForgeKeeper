"""
Unit tests for the config_merger.merge_config function.

Validates: Requirements 7.2, 7.3

Tests cover:
- Merging with no conflicts (disjoint env vars)
- Merging with conflicts (user value wins, warning generated)
- Merging with empty imported config
- Merging with empty user config
- Both configs empty
- Language merging (union of both sets)
- Port merging (union with no duplicates)
- Same key, same value (no warning generated)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from config_merger import merge_config


class TestMergeNoConflicts:
    """Merging with no conflicts - disjoint env vars should all appear."""

    def test_disjoint_env_vars_all_present(self):
        user = {'env_vars': {'USER_VAR': 'uval'}}
        imported = {'env_vars': {'IMPORTED_VAR': 'ival'}}

        result = merge_config(user, imported)

        assert result['env_vars'] == {'USER_VAR': 'uval', 'IMPORTED_VAR': 'ival'}
        assert result['warnings'] == []

    def test_multiple_disjoint_env_vars(self):
        user = {'env_vars': {'A': '1', 'B': '2'}}
        imported = {'env_vars': {'C': '3', 'D': '4'}}

        result = merge_config(user, imported)

        assert result['env_vars'] == {'A': '1', 'B': '2', 'C': '3', 'D': '4'}
        assert result['warnings'] == []


class TestMergeWithConflicts:
    """Merging with conflicts - same key, different values, user wins, warning generated."""

    def test_user_value_wins_on_conflict(self):
        user = {'env_vars': {'SHARED': 'user_val'}}
        imported = {'env_vars': {'SHARED': 'imported_val'}}

        result = merge_config(user, imported)

        assert result['env_vars']['SHARED'] == 'user_val'

    def test_warning_generated_on_conflict(self):
        user = {'env_vars': {'SHARED': 'user_val'}}
        imported = {'env_vars': {'SHARED': 'imported_val'}}

        result = merge_config(user, imported)

        assert len(result['warnings']) == 1
        assert 'SHARED' in result['warnings'][0]
        assert 'user_val' in result['warnings'][0]
        assert 'imported_val' in result['warnings'][0]

    def test_multiple_conflicts_generate_multiple_warnings(self):
        user = {'env_vars': {'X': 'u1', 'Y': 'u2'}}
        imported = {'env_vars': {'X': 'i1', 'Y': 'i2'}}

        result = merge_config(user, imported)

        assert len(result['warnings']) == 2
        assert result['env_vars']['X'] == 'u1'
        assert result['env_vars']['Y'] == 'u2'


class TestMergeEmptyImported:
    """Merging with empty imported config - user config passes through unchanged."""

    def test_user_env_vars_pass_through(self):
        user = {'env_vars': {'MY_VAR': 'val'}, 'languages': ['python'], 'ports': [8080]}
        imported = {}

        result = merge_config(user, imported)

        assert result['env_vars'] == {'MY_VAR': 'val'}
        assert result['languages'] == ['python']
        assert result['ports'] == [8080]
        assert result['warnings'] == []

    def test_empty_imported_env_vars(self):
        user = {'env_vars': {'A': '1'}}
        imported = {'env_vars': {}}

        result = merge_config(user, imported)

        assert result['env_vars'] == {'A': '1'}
        assert result['warnings'] == []


class TestMergeEmptyUser:
    """Merging with empty user config - imported config passes through."""

    def test_imported_env_vars_pass_through(self):
        user = {}
        imported = {'env_vars': {'IMPORTED': 'val'}, 'languages': ['node'], 'ports': [3000]}

        result = merge_config(user, imported)

        assert result['env_vars'] == {'IMPORTED': 'val'}
        assert result['languages'] == ['node']
        assert result['ports'] == [3000]
        assert result['warnings'] == []


class TestMergeBothEmpty:
    """Both configs empty - result has empty env_vars, languages, ports."""

    def test_both_empty(self):
        result = merge_config({}, {})

        assert result['env_vars'] == {}
        assert result['languages'] == []
        assert result['ports'] == []
        assert result['warnings'] == []


class TestLanguageMerging:
    """Language merging - union of both sets."""

    def test_union_of_languages(self):
        user = {'languages': ['python', 'go']}
        imported = {'languages': ['node', 'rust']}

        result = merge_config(user, imported)

        assert set(result['languages']) == {'python', 'go', 'node', 'rust'}

    def test_no_duplicate_languages(self):
        user = {'languages': ['python', 'node']}
        imported = {'languages': ['node', 'rust']}

        result = merge_config(user, imported)

        assert sorted(result['languages']) == ['node', 'python', 'rust']

    def test_languages_sorted(self):
        user = {'languages': ['rust', 'go']}
        imported = {'languages': ['python', 'node']}

        result = merge_config(user, imported)

        assert result['languages'] == sorted(result['languages'])


class TestPortMerging:
    """Port merging - union with no duplicates."""

    def test_union_of_ports(self):
        user = {'ports': [8080, 3000]}
        imported = {'ports': [5432, 6379]}

        result = merge_config(user, imported)

        assert set(result['ports']) == {8080, 3000, 5432, 6379}

    def test_no_duplicate_ports(self):
        user = {'ports': [8080, 3000]}
        imported = {'ports': [3000, 5432]}

        result = merge_config(user, imported)

        assert sorted(result['ports']) == [3000, 5432, 8080]

    def test_port_order_user_first(self):
        user = {'ports': [8080]}
        imported = {'ports': [3000]}

        result = merge_config(user, imported)

        assert result['ports'] == [8080, 3000]


class TestSameKeySameValue:
    """Same key, same value - no warning generated (not a conflict)."""

    def test_no_warning_when_values_match(self):
        user = {'env_vars': {'SHARED': 'same'}}
        imported = {'env_vars': {'SHARED': 'same'}}

        result = merge_config(user, imported)

        assert result['env_vars']['SHARED'] == 'same'
        assert result['warnings'] == []
