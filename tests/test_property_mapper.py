"""
Property-based tests for DevcontainerMapper.

# Feature: devcontainer-import, Property 3: Language Feature Mapping
# Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9

Uses Hypothesis to generate devcontainer configs with random subsets of known
language features and verify that each feature maps to the correct ForgeKeeper
language runtime.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from hypothesis import given, settings
import hypothesis.strategies as st

from devcontainer_parser import DevcontainerConfig
from devcontainer_mapper import DevcontainerMapper


# --- Known language feature IDs and their expected ForgeKeeper language ---

# Each entry: (feature_id_prefix, version_suffix_examples, expected_language)
LANGUAGE_FEATURES = {
    'python': [
        'ghcr.io/devcontainers/features/python',
        'ghcr.io/devcontainers-contrib/features/python',
    ],
    'node': [
        'ghcr.io/devcontainers/features/node',
        'ghcr.io/devcontainers-contrib/features/node',
    ],
    'go': [
        'ghcr.io/devcontainers/features/go',
        'ghcr.io/devcontainers-contrib/features/go',
    ],
    'rust': [
        'ghcr.io/devcontainers/features/rust',
        'ghcr.io/devcontainers-contrib/features/rust',
    ],
    'java': [
        'ghcr.io/devcontainers/features/java',
        'ghcr.io/devcontainers-contrib/features/java',
    ],
    'dotnet': [
        'ghcr.io/devcontainers/features/dotnet',
        'ghcr.io/microsoft/devcontainers/features/dotnet',
    ],
    'ruby': [
        'ghcr.io/devcontainers/features/ruby',
        'ghcr.io/devcontainers-contrib/features/ruby',
    ],
    'php': [
        'ghcr.io/devcontainers/features/php',
        'ghcr.io/devcontainers-contrib/features/php',
    ],
}

# Flatten to a list of (feature_id_prefix, expected_language) tuples
ALL_FEATURE_LANGUAGE_PAIRS = []
for lang, prefixes in LANGUAGE_FEATURES.items():
    for prefix in prefixes:
        ALL_FEATURE_LANGUAGE_PAIRS.append((prefix, lang))

# Version suffixes that can be appended to feature IDs
VERSION_SUFFIXES = ['', ':1', ':2', ':latest', ':1.0', ':3.11']


# --- Strategies ---


# Strategy for a single language feature: picks a known prefix and appends a version suffix
feature_with_language_st = st.sampled_from(ALL_FEATURE_LANGUAGE_PAIRS).flatmap(
    lambda pair: st.sampled_from(VERSION_SUFFIXES).map(
        lambda suffix: (pair[0] + suffix, pair[1])
    )
)

# Strategy for feature option values (version, etc.)
feature_options_st = st.fixed_dictionaries({}, optional={
    "version": st.text(alphabet="0123456789.", min_size=1, max_size=10),
})


@st.composite
def language_features_subset_st(draw):
    """
    Generate a non-empty list of (feature_id, expected_language) pairs
    by drawing a random subset of known language features.
    """
    features = draw(
        st.lists(feature_with_language_st, min_size=1, max_size=8, unique_by=lambda x: x[0])
    )
    return features


@st.composite
def devcontainer_config_with_languages_st(draw):
    """
    Generate a DevcontainerConfig populated with a random subset of known
    language features. Returns (config, expected_languages) tuple.
    """
    feature_pairs = draw(language_features_subset_st())

    features_dict = {}
    expected_languages = set()
    for feature_id, expected_lang in feature_pairs:
        features_dict[feature_id] = draw(feature_options_st)
        expected_languages.add(expected_lang)

    config = DevcontainerConfig(
        features=features_dict,
        customizations={},
        forward_ports=[],
        remote_env={},
        image=None,
        dockerfile=None,
        raw={},
    )
    return config, expected_languages


# --- Property Tests ---

class TestPropertyLanguageFeatureMapping:
    """
    Property 3: Language Feature Mapping

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9**

    For any devcontainer.json containing language features (Python, Node.js, Go,
    Rust, Java, .NET, Ruby, PHP), the mapper should correctly identify and select
    the corresponding ForgeKeeper language runtime.
    """
    # Feature: devcontainer-import, Property 3: Language Feature Mapping

    def setup_method(self):
        self.mapper = DevcontainerMapper()

    @given(data=devcontainer_config_with_languages_st())
    @settings(max_examples=100)
    def test_all_known_features_are_detected(self, data):
        """
        # Feature: devcontainer-import, Property 3: Language Feature Mapping
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9**

        For any devcontainer config with known language features, the mapper
        should detect all expected languages.
        """
        config, expected_languages = data
        result = self.mapper.map_features(config)

        assert expected_languages.issubset(result.languages), (
            f"Expected languages {expected_languages} but got {result.languages}. "
            f"Missing: {expected_languages - result.languages}"
        )

    @given(data=devcontainer_config_with_languages_st())
    @settings(max_examples=100)
    def test_no_unrecognized_for_known_features(self, data):
        """
        # Feature: devcontainer-import, Property 3: Language Feature Mapping
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9**

        For any devcontainer config containing only known language features,
        the mapper should produce no unrecognized features.
        """
        config, _ = data
        result = self.mapper.map_features(config)

        assert result.unrecognized_features == [], (
            f"Known features were marked unrecognized: {result.unrecognized_features}"
        )

    @given(data=devcontainer_config_with_languages_st())
    @settings(max_examples=100)
    def test_detected_languages_are_only_expected_ones(self, data):
        """
        # Feature: devcontainer-import, Property 3: Language Feature Mapping
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9**

        For any devcontainer config with known language features and no image,
        the detected languages should exactly match the expected set.
        """
        config, expected_languages = data
        result = self.mapper.map_features(config)

        assert result.languages == expected_languages, (
            f"Expected exactly {expected_languages} but got {result.languages}. "
            f"Extra: {result.languages - expected_languages}, "
            f"Missing: {expected_languages - result.languages}"
        )

    @given(feature_pair=feature_with_language_st)
    @settings(max_examples=100)
    def test_each_individual_feature_maps_correctly(self, feature_pair):
        """
        # Feature: devcontainer-import, Property 3: Language Feature Mapping
        **Validates: Requirements 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9**

        For any single known language feature, the mapper should identify
        exactly the corresponding ForgeKeeper language runtime.
        """
        feature_id, expected_lang = feature_pair
        config = DevcontainerConfig(
            features={feature_id: {}},
            customizations={},
            forward_ports=[],
            remote_env={},
            image=None,
            dockerfile=None,
            raw={},
        )
        result = self.mapper.map_features(config)

        assert expected_lang in result.languages, (
            f"Feature '{feature_id}' should map to '{expected_lang}' "
            f"but got {result.languages}"
        )
        assert len(result.languages) == 1, (
            f"Single feature '{feature_id}' should map to exactly one language "
            f"but got {result.languages}"
        )

# --- All known feature prefixes (used to filter out recognized features) ---

ALL_KNOWN_PREFIXES = []
for _prefixes in LANGUAGE_FEATURES.values():
    ALL_KNOWN_PREFIXES.extend(_prefixes)


def _is_recognized(feature_id: str) -> bool:
    """Return True if feature_id starts with any known prefix."""
    return any(feature_id.startswith(p) for p in ALL_KNOWN_PREFIXES)


# Strategy for generating feature IDs that do NOT match any known pattern.
# Uses realistic-looking ghcr.io paths with names that aren't in the mapping.
_UNRECOGNIZED_NAMES = [
    'docker-in-docker',
    'docker-outside-of-docker',
    'kubectl-helm-minikube',
    'terraform',
    'aws-cli',
    'azure-cli',
    'github-cli',
    'common-utils',
    'git',
    'git-lfs',
    'sshd',
    'desktop-lite',
    'nvidia-cuda',
    'powershell',
    'homebrew',
    'nix',
    'conda',
    'cmake',
    'bazel',
]

_UNRECOGNIZED_REGISTRIES = [
    'ghcr.io/devcontainers/features/',
    'ghcr.io/devcontainers-contrib/features/',
    'ghcr.io/someorg/features/',
    'ghcr.io/custom/',
]

unrecognized_feature_id_st = st.builds(
    lambda registry, name, suffix: registry + name + suffix,
    registry=st.sampled_from(_UNRECOGNIZED_REGISTRIES),
    name=st.sampled_from(_UNRECOGNIZED_NAMES),
    suffix=st.sampled_from(VERSION_SUFFIXES),
).filter(lambda fid: not _is_recognized(fid))


@st.composite
def devcontainer_config_with_unrecognized_st(draw):
    """
    Generate a DevcontainerConfig populated exclusively with unrecognized
    features (none matching any known language prefix).
    Returns (config, list_of_unrecognized_feature_ids).
    """
    feature_ids = draw(
        st.lists(unrecognized_feature_id_st, min_size=1, max_size=8, unique=True)
    )

    features_dict = {}
    for fid in feature_ids:
        features_dict[fid] = draw(feature_options_st)

    config = DevcontainerConfig(
        features=features_dict,
        customizations={},
        forward_ports=[],
        remote_env={},
        image=None,
        dockerfile=None,
        raw={},
    )
    return config, feature_ids


# --- Property 4 Tests ---

class TestPropertyUnrecognizedFeatureHandling:
    """
    Property 4: Unrecognized Feature Handling

    **Validates: Requirements 3.10**

    For any devcontainer.json containing features not in the known mapping list,
    the mapper should log them as unrecognized and include them in the warnings
    list without failing the import.
    """
    # Feature: devcontainer-import, Property 4: Unrecognized Feature Handling

    def setup_method(self):
        self.mapper = DevcontainerMapper()

    @given(data=devcontainer_config_with_unrecognized_st())
    @settings(max_examples=100)
    def test_unrecognized_features_are_recorded(self, data):
        """
        # Feature: devcontainer-import, Property 4: Unrecognized Feature Handling
        **Validates: Requirements 3.10**

        For any devcontainer config with only unrecognized features, every
        feature should appear in result.unrecognized_features.
        """
        config, unrecognized_ids = data
        result = self.mapper.map_features(config)

        assert set(result.unrecognized_features) == set(unrecognized_ids), (
            f"Expected unrecognized {unrecognized_ids} but got {result.unrecognized_features}"
        )

    @given(data=devcontainer_config_with_unrecognized_st())
    @settings(max_examples=100)
    def test_warnings_generated_for_each_unrecognized(self, data):
        """
        # Feature: devcontainer-import, Property 4: Unrecognized Feature Handling
        **Validates: Requirements 3.10**

        For any devcontainer config with unrecognized features, a warning
        should be generated for each one.
        """
        config, unrecognized_ids = data
        result = self.mapper.map_features(config)

        assert len(result.warnings) == len(unrecognized_ids), (
            f"Expected {len(unrecognized_ids)} warnings but got {len(result.warnings)}"
        )
        for fid in unrecognized_ids:
            assert any(fid in w for w in result.warnings), (
                f"No warning found mentioning unrecognized feature '{fid}'"
            )

    @given(data=devcontainer_config_with_unrecognized_st())
    @settings(max_examples=100)
    def test_import_does_not_fail(self, data):
        """
        # Feature: devcontainer-import, Property 4: Unrecognized Feature Handling
        **Validates: Requirements 3.10**

        For any devcontainer config with unrecognized features, the mapper
        should still return a valid MappingResult (no exception, valid structure).
        """
        config, _ = data
        result = self.mapper.map_features(config)

        # Result is a valid MappingResult with expected types
        assert isinstance(result.languages, set)
        assert isinstance(result.env_vars, dict)
        assert isinstance(result.ports, list)
        assert isinstance(result.unrecognized_features, list)
        assert isinstance(result.warnings, list)

    @given(data=devcontainer_config_with_unrecognized_st())
    @settings(max_examples=100)
    def test_no_languages_detected_for_unrecognized_only(self, data):
        """
        # Feature: devcontainer-import, Property 4: Unrecognized Feature Handling
        **Validates: Requirements 3.10**

        For any devcontainer config with only unrecognized features and no image,
        no languages should be detected.
        """
        config, _ = data
        result = self.mapper.map_features(config)

        assert len(result.languages) == 0, (
            f"Expected no languages for unrecognized-only config but got {result.languages}"
        )

