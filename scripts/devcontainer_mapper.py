#!/usr/bin/env python3
"""
Devcontainer Mapper Module

Maps devcontainer features to ForgeKeeper language runtimes.
Translates devcontainer.json configuration to ForgeKeeper's modular language system.
"""
from dataclasses import dataclass, field
from typing import Any

from devcontainer_parser import DevcontainerConfig


@dataclass
class MappingResult:
    """Result of mapping devcontainer config to ForgeKeeper."""
    languages: set[str] = field(default_factory=set)
    env_vars: dict[str, str] = field(default_factory=dict)
    ports: list[int] = field(default_factory=list)
    unrecognized_features: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class DevcontainerMapper:
    """Maps devcontainer features to ForgeKeeper language runtimes."""
    
    # Feature ID patterns that map to ForgeKeeper languages.
    # Keys are ForgeKeeper runtime IDs; values are prefix patterns matched
    # against devcontainer feature IDs (e.g. "ghcr.io/devcontainers/features/python:1"
    # matches the "ghcr.io/devcontainers/features/python" prefix → python runtime).
    FEATURE_MAPPINGS = {
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
    
    def map_features(self, config: DevcontainerConfig) -> MappingResult:
        """
        Map devcontainer features to ForgeKeeper languages.

        Args:
            config: Parsed devcontainer configuration

        Returns:
            MappingResult with detected languages and warnings
        """
        result = MappingResult()

        # Iterate over features and match against known patterns
        for feature_id in config.features:
            matched = False
            for language, patterns in self.FEATURE_MAPPINGS.items():
                for pattern in patterns:
                    if feature_id.startswith(pattern):
                        result.languages.add(language)
                        matched = True
                        break
                if matched:
                    break
            if not matched:
                result.unrecognized_features.append(feature_id)
                result.warnings.append(
                    f"Feature '{feature_id}' not mapped to any ForgeKeeper language runtime"
                )

        # Detect languages from base image if set
        if config.image:
            for lang in self.detect_language_from_image(config.image):
                result.languages.add(lang)

        # Copy environment variables
        result.env_vars = dict(config.remote_env)

        # Copy forwarded ports
        result.ports = list(config.forward_ports)

        return result
    
    def detect_language_from_image(self, image: str) -> list[str]:
        """
        Detect languages from base image name.

        Parses Docker image names for language hints. Handles various formats
        including registry prefixes and tags (e.g. 'python:3.11',
        'mcr.microsoft.com/devcontainers/python:3.11', 'node:20-bullseye').

        Args:
            image: Docker image name

        Returns:
            List of detected ForgeKeeper language IDs
        """
        # Map of keywords found in image names to ForgeKeeper language IDs
        IMAGE_LANGUAGE_KEYWORDS = {
            'python': 'python',
            'node': 'node',
            'golang': 'go',
            'go': 'go',
            'rust': 'rust',
            'java': 'java',
            'dotnet': 'dotnet',
            'ruby': 'ruby',
            'php': 'php',
            'swift': 'swift',
            'dart': 'dart',
        }

        if not image or not image.strip():
            return []

        # Normalize: lowercase and strip the tag/digest portion
        image_lower = image.lower().strip()
        # Remove tag (:...) or digest (@sha256:...)
        image_path = image_lower.split('@')[0].split(':')[0]

        # Split into path segments (handles registries like mcr.microsoft.com/devcontainers/python)
        segments = image_path.split('/')

        detected: list[str] = []
        seen: set[str] = set()

        for segment in segments:
            # Split segment on hyphens/underscores to match individual words
            # e.g. "python-slim" -> ["python", "slim"]
            parts = segment.replace('_', '-').split('-')
            for part in parts:
                if part in IMAGE_LANGUAGE_KEYWORDS:
                    lang_id = IMAGE_LANGUAGE_KEYWORDS[part]
                    if lang_id not in seen:
                        seen.add(lang_id)
                        detected.append(lang_id)

        return detected
