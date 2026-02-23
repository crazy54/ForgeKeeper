#!/usr/bin/env python3
"""
Configuration Merger Module

Merges user-provided configuration with imported devcontainer configuration.
Implements priority logic: User inputs > Imported values > Defaults.
Tracks conflicts and produces warnings when environment variables collide.
"""
from typing import Any


def merge_config(user_config: dict, imported_config: dict) -> dict:
    """
    Merge user-provided config with imported devcontainer config.

    Priority: User inputs > Imported values > Defaults

    Args:
        user_config: Configuration from wizard form (dict with 'env_vars', 'languages', etc.)
        imported_config: Imported configuration (dict with 'env_vars', 'languages', 'ports', etc.)

    Returns:
        Merged configuration dictionary with 'warnings' list for conflicts
    """
    merged = {}
    warnings: list[str] = []

    # --- Environment variables ---
    user_env = user_config.get('env_vars', {})
    imported_env = imported_config.get('env_vars', {})

    merged_env: dict[str, str] = {}

    # Start with imported env vars
    for key, value in imported_env.items():
        merged_env[key] = value

    # Layer user env vars on top; detect conflicts
    for key, value in user_env.items():
        if key in imported_env and imported_env[key] != value:
            warnings.append(
                f"Environment variable '{key}' conflict: "
                f"keeping user value '{value}' over imported value '{imported_env[key]}'"
            )
        merged_env[key] = value

    merged['env_vars'] = merged_env

    # --- Languages (union of both sets, no duplicates) ---
    user_langs = set(user_config.get('languages', []))
    imported_langs = set(imported_config.get('languages', []))
    merged['languages'] = sorted(user_langs | imported_langs)

    # --- Ports (union of both lists, no duplicates) ---
    user_ports = user_config.get('ports', [])
    imported_ports = imported_config.get('ports', [])
    seen_ports: set[int] = set()
    merged_ports: list[int] = []
    for port in list(user_ports) + list(imported_ports):
        if port not in seen_ports:
            seen_ports.add(port)
            merged_ports.append(port)
    merged['ports'] = merged_ports

    # --- Carry forward any other user config keys not already handled ---
    handled_keys = {'env_vars', 'languages', 'ports'}
    for key, value in user_config.items():
        if key not in handled_keys:
            merged[key] = value

    # --- Carry forward any other imported config keys not already handled ---
    for key, value in imported_config.items():
        if key not in handled_keys and key not in merged:
            merged[key] = value

    merged['warnings'] = warnings
    return merged
