#!/usr/bin/env python3
"""Unit tests for DevcontainerMapper.map_features() method."""
import sys
import os
import pytest

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from devcontainer_parser import DevcontainerConfig
from devcontainer_mapper import DevcontainerMapper, MappingResult


class TestMapFeatures:
    """Tests for the map_features() method."""

    def setup_method(self):
        self.mapper = DevcontainerMapper()

    def test_single_python_feature(self):
        config = DevcontainerConfig(
            features={'ghcr.io/devcontainers/features/python:1': {'version': '3.11'}}
        )
        result = self.mapper.map_features(config)
        assert 'python' in result.languages
        assert len(result.unrecognized_features) == 0

    def test_single_node_feature(self):
        config = DevcontainerConfig(
            features={'ghcr.io/devcontainers/features/node:1': {'version': '20'}}
        )
        result = self.mapper.map_features(config)
        assert 'node' in result.languages

    def test_multiple_language_features(self):
        config = DevcontainerConfig(
            features={
                'ghcr.io/devcontainers/features/python:1': {},
                'ghcr.io/devcontainers/features/node:1': {},
                'ghcr.io/devcontainers/features/go:1': {},
            }
        )
        result = self.mapper.map_features(config)
        assert result.languages == {'python', 'node', 'go'}

    def test_all_supported_languages(self):
        config = DevcontainerConfig(
            features={
                'ghcr.io/devcontainers/features/python:1': {},
                'ghcr.io/devcontainers/features/node:1': {},
                'ghcr.io/devcontainers/features/go:1': {},
                'ghcr.io/devcontainers/features/rust:1': {},
                'ghcr.io/devcontainers/features/java:1': {},
                'ghcr.io/devcontainers/features/dotnet:1': {},
                'ghcr.io/devcontainers/features/ruby:1': {},
                'ghcr.io/devcontainers/features/php:1': {},
            }
        )
        result = self.mapper.map_features(config)
        expected = {'python', 'node', 'go', 'rust', 'java', 'dotnet', 'ruby', 'php'}
        assert result.languages == expected
        assert len(result.unrecognized_features) == 0
        assert len(result.warnings) == 0

    def test_contrib_feature_patterns(self):
        config = DevcontainerConfig(
            features={
                'ghcr.io/devcontainers-contrib/features/python:1': {},
                'ghcr.io/devcontainers-contrib/features/node:2': {},
            }
        )
        result = self.mapper.map_features(config)
        assert result.languages == {'python', 'node'}

    def test_dotnet_microsoft_pattern(self):
        config = DevcontainerConfig(
            features={'ghcr.io/microsoft/devcontainers/features/dotnet:1': {}}
        )
        result = self.mapper.map_features(config)
        assert 'dotnet' in result.languages

    def test_unrecognized_feature_logged(self):
        config = DevcontainerConfig(
            features={'ghcr.io/devcontainers/features/docker-in-docker:2': {}}
        )
        result = self.mapper.map_features(config)
        assert len(result.languages) == 0
        assert 'ghcr.io/devcontainers/features/docker-in-docker:2' in result.unrecognized_features
        assert len(result.warnings) == 1
        assert 'docker-in-docker' in result.warnings[0]

    def test_mixed_recognized_and_unrecognized(self):
        config = DevcontainerConfig(
            features={
                'ghcr.io/devcontainers/features/python:1': {},
                'ghcr.io/devcontainers/features/docker-in-docker:2': {},
                'ghcr.io/some-org/custom-feature:1': {},
            }
        )
        result = self.mapper.map_features(config)
        assert result.languages == {'python'}
        assert len(result.unrecognized_features) == 2
        assert len(result.warnings) == 2

    def test_empty_features(self):
        config = DevcontainerConfig(features={})
        result = self.mapper.map_features(config)
        assert len(result.languages) == 0
        assert len(result.unrecognized_features) == 0
        assert len(result.warnings) == 0

    def test_env_vars_copied(self):
        config = DevcontainerConfig(
            features={},
            remote_env={'MY_VAR': 'value1', 'OTHER': 'value2'},
        )
        result = self.mapper.map_features(config)
        assert result.env_vars == {'MY_VAR': 'value1', 'OTHER': 'value2'}

    def test_env_vars_are_independent_copy(self):
        env = {'KEY': 'val'}
        config = DevcontainerConfig(features={}, remote_env=env)
        result = self.mapper.map_features(config)
        result.env_vars['NEW'] = 'added'
        assert 'NEW' not in config.remote_env

    def test_ports_copied(self):
        config = DevcontainerConfig(
            features={},
            forward_ports=[3000, 8080, 5432],
        )
        result = self.mapper.map_features(config)
        assert result.ports == [3000, 8080, 5432]

    def test_ports_are_independent_copy(self):
        ports = [3000]
        config = DevcontainerConfig(features={}, forward_ports=ports)
        result = self.mapper.map_features(config)
        result.ports.append(9999)
        assert 9999 not in config.forward_ports

    def test_image_triggers_detection(self):
        config = DevcontainerConfig(
            features={},
            image='mcr.microsoft.com/devcontainers/python:3.11',
        )
        # detect_language_from_image is a stub returning [] for now (task 3.3)
        result = self.mapper.map_features(config)
        assert isinstance(result, MappingResult)

    def test_no_image_skips_detection(self):
        config = DevcontainerConfig(features={}, image=None)
        result = self.mapper.map_features(config)
        assert isinstance(result, MappingResult)

    def test_prefix_matching_with_version_suffix(self):
        """Feature IDs with version tags should still match via prefix."""
        config = DevcontainerConfig(
            features={
                'ghcr.io/devcontainers/features/python:3': {},
                'ghcr.io/devcontainers/features/rust:latest': {},
            }
        )
        result = self.mapper.map_features(config)
        assert result.languages == {'python', 'rust'}

    def test_result_type(self):
        config = DevcontainerConfig(features={})
        result = self.mapper.map_features(config)
        assert isinstance(result, MappingResult)
        assert isinstance(result.languages, set)
        assert isinstance(result.env_vars, dict)
        assert isinstance(result.ports, list)
        assert isinstance(result.unrecognized_features, list)
        assert isinstance(result.warnings, list)


class TestDetectLanguageFromImage:
    """Tests for the detect_language_from_image() method."""

    def setup_method(self):
        self.mapper = DevcontainerMapper()

    def test_python_with_tag(self):
        assert self.mapper.detect_language_from_image('python:3.11') == ['python']

    def test_node_with_tag(self):
        assert self.mapper.detect_language_from_image('node:20-bullseye') == ['node']

    def test_golang_maps_to_go(self):
        assert self.mapper.detect_language_from_image('golang:1.21') == ['go']

    def test_go_keyword(self):
        assert self.mapper.detect_language_from_image('go:1.21') == ['go']

    def test_rust_image(self):
        assert self.mapper.detect_language_from_image('rust:1.75') == ['rust']

    def test_java_image(self):
        assert self.mapper.detect_language_from_image('java:17') == ['java']

    def test_dotnet_image(self):
        assert self.mapper.detect_language_from_image('dotnet:8.0') == ['dotnet']

    def test_ruby_image(self):
        assert self.mapper.detect_language_from_image('ruby:3.2') == ['ruby']

    def test_php_image(self):
        assert self.mapper.detect_language_from_image('php:8.2') == ['php']

    def test_swift_image(self):
        assert self.mapper.detect_language_from_image('swift:5.9') == ['swift']

    def test_dart_image(self):
        assert self.mapper.detect_language_from_image('dart:3.2') == ['dart']

    def test_registry_prefix(self):
        """Image with full registry path should still detect language."""
        result = self.mapper.detect_language_from_image('mcr.microsoft.com/devcontainers/python:3.11')
        assert result == ['python']

    def test_no_language_detected(self):
        """Generic OS images should return empty list."""
        assert self.mapper.detect_language_from_image('ubuntu:22.04') == []

    def test_case_insensitive(self):
        assert self.mapper.detect_language_from_image('Python:3.11') == ['python']
        assert self.mapper.detect_language_from_image('NODE:20') == ['node']

    def test_empty_string(self):
        assert self.mapper.detect_language_from_image('') == []

    def test_none_input(self):
        assert self.mapper.detect_language_from_image(None) == []

    def test_whitespace_only(self):
        assert self.mapper.detect_language_from_image('   ') == []

    def test_image_with_digest(self):
        result = self.mapper.detect_language_from_image('python@sha256:abc123')
        assert result == ['python']

    def test_hyphenated_variant(self):
        """Language name as prefix in hyphenated image name."""
        result = self.mapper.detect_language_from_image('python-slim:3.11')
        assert result == ['python']

    def test_no_duplicate_languages(self):
        """Same language appearing in multiple segments should only appear once."""
        result = self.mapper.detect_language_from_image('registry.io/python/python:3.11')
        assert result == ['python']

    def test_image_with_no_tag(self):
        assert self.mapper.detect_language_from_image('python') == ['python']

    def test_map_features_integrates_image_detection(self):
        """map_features should include languages detected from image."""
        config = DevcontainerConfig(
            features={},
            image='mcr.microsoft.com/devcontainers/python:3.11',
        )
        result = self.mapper.map_features(config)
        assert 'python' in result.languages


class TestMapperEdgeCases:
    """Edge case tests for DevcontainerMapper.

    Validates: Requirements 3.1, 3.10, 9.4
    """

    def setup_method(self):
        self.mapper = DevcontainerMapper()

    # --- No language features (only non-language features) ---

    def test_only_non_language_features(self):
        """Devcontainer with only non-language features should detect no languages."""
        config = DevcontainerConfig(
            features={
                'ghcr.io/devcontainers/features/docker-in-docker:2': {},
                'ghcr.io/devcontainers/features/git:1': {},
                'ghcr.io/devcontainers/features/github-cli:1': {},
            }
        )
        result = self.mapper.map_features(config)
        assert len(result.languages) == 0
        assert len(result.unrecognized_features) == 3
        assert len(result.warnings) == 3

    def test_no_language_features_no_image(self):
        """No language features and no image should yield empty languages."""
        config = DevcontainerConfig(
            features={'ghcr.io/devcontainers/features/docker-in-docker:2': {}},
            image=None,
        )
        result = self.mapper.map_features(config)
        assert len(result.languages) == 0

    # --- Multiple languages from features AND image ---

    def test_languages_from_features_and_image_combined(self):
        """Languages detected from both features and image should be merged."""
        config = DevcontainerConfig(
            features={'ghcr.io/devcontainers/features/node:1': {}},
            image='mcr.microsoft.com/devcontainers/python:3.11',
        )
        result = self.mapper.map_features(config)
        assert 'node' in result.languages
        assert 'python' in result.languages
        assert len(result.languages) == 2

    def test_duplicate_language_from_feature_and_image(self):
        """Same language from feature and image should not duplicate."""
        config = DevcontainerConfig(
            features={'ghcr.io/devcontainers/features/python:1': {}},
            image='python:3.11',
        )
        result = self.mapper.map_features(config)
        assert result.languages == {'python'}

    def test_multiple_languages_from_features_plus_image(self):
        """Several feature languages plus image language all detected."""
        config = DevcontainerConfig(
            features={
                'ghcr.io/devcontainers/features/go:1': {},
                'ghcr.io/devcontainers/features/rust:1': {},
            },
            image='node:20',
        )
        result = self.mapper.map_features(config)
        assert result.languages == {'go', 'rust', 'node'}

    # --- Feature with no version suffix ---

    def test_feature_without_version_suffix(self):
        """Feature ID with no version tag should still match via prefix."""
        config = DevcontainerConfig(
            features={'ghcr.io/devcontainers/features/python': {}}
        )
        result = self.mapper.map_features(config)
        assert 'python' in result.languages
        assert len(result.unrecognized_features) == 0

    def test_contrib_feature_without_version_suffix(self):
        """Contrib feature ID with no version tag should still match."""
        config = DevcontainerConfig(
            features={'ghcr.io/devcontainers-contrib/features/ruby': {}}
        )
        result = self.mapper.map_features(config)
        assert 'ruby' in result.languages

    # --- Only image, no features, detects a language ---

    def test_only_image_detects_language(self):
        """Devcontainer with only an image (no features) should detect language from image."""
        config = DevcontainerConfig(
            features={},
            image='golang:1.21',
        )
        result = self.mapper.map_features(config)
        assert 'go' in result.languages
        assert len(result.unrecognized_features) == 0
        assert len(result.warnings) == 0

    def test_only_image_no_language_detected(self):
        """Image with no language hint should yield empty languages."""
        config = DevcontainerConfig(
            features={},
            image='ubuntu:22.04',
        )
        result = self.mapper.map_features(config)
        assert len(result.languages) == 0

    # --- Image name parsing edge cases ---

    def test_image_with_port_in_registry(self):
        """Image with port in registry: colon-based tag stripping truncates the path.

        'registry.local:5000/python:3.11' becomes 'registry.local' after
        split(':')[0], so the /python segment is lost. This is a known
        limitation of the simple parsing approach.
        """
        result = self.mapper.detect_language_from_image('registry.local:5000/python:3.11')
        # Language is NOT detected because the colon split removes the path
        assert result == []

    def test_image_with_deeply_nested_path(self):
        """Image with many path segments should still detect language."""
        result = self.mapper.detect_language_from_image('ghcr.io/org/team/subgroup/node:20')
        assert 'node' in result

    def test_image_underscore_variant(self):
        """Language name with underscore separator should be detected."""
        result = self.mapper.detect_language_from_image('my_python_image:latest')
        assert 'python' in result

    def test_image_multiple_languages_in_name(self):
        """Image name containing multiple language keywords should detect all."""
        result = self.mapper.detect_language_from_image('python-node:latest')
        assert 'python' in result
        assert 'node' in result
