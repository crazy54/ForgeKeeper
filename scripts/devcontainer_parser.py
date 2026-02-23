#!/usr/bin/env python3
"""
Devcontainer Parser Module

Parses and validates devcontainer.json files according to the devcontainer specification.
Extracts configuration including features, customizations, ports, and environment variables.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

try:
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    # jsonschema is optional - validation will be basic if not available
    validate = None
    ValidationError = None
    Draft7Validator = None


@dataclass
class DevcontainerConfig:
    """Extracted devcontainer configuration."""
    features: dict[str, Any] = field(default_factory=dict)
    customizations: dict[str, Any] = field(default_factory=dict)
    forward_ports: list[int] = field(default_factory=list)
    remote_env: dict[str, str] = field(default_factory=dict)
    image: Optional[str] = None
    dockerfile: Optional[str] = None
    raw: dict = field(default_factory=dict)


@dataclass
class ParseResult:
    """Result of parsing a devcontainer.json file."""
    success: bool
    config: Optional[DevcontainerConfig] = None
    errors: list[str] = field(default_factory=list)


class DevcontainerParser:
    """Parses and validates devcontainer.json files."""
    
    # Basic schema for devcontainer.json validation
    # Based on https://containers.dev/implementors/json_schema/
    DEVCONTAINER_SCHEMA = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "image": {"type": "string"},
            "dockerfile": {"type": "string"},
            "build": {"type": "object"},
            "features": {
                "type": "object",
                "additionalProperties": True
            },
            "customizations": {
                "type": "object",
                "additionalProperties": True
            },
            "forwardPorts": {
                "type": "array",
                "items": {"type": ["integer", "string", "null"]}
            },
            "remoteEnv": {
                "type": "object",
                "additionalProperties": {"type": "string"}
            },
            "remoteUser": {"type": "string"},
            "containerEnv": {
                "type": "object",
                "additionalProperties": {"type": "string"}
            },
            "containerUser": {"type": "string"},
            "updateRemoteUserUID": {"type": "boolean"},
            "mounts": {"type": "array"},
            "runArgs": {"type": "array"},
            "shutdownAction": {"type": "string"},
            "overrideCommand": {"type": "boolean"},
            "workspaceFolder": {"type": "string"},
            "workspaceMount": {"type": "string"}
        },
        "additionalProperties": True
    }
    
    def parse_file(self, file_path: str) -> ParseResult:
        """
        Parse a devcontainer.json file from disk.
        
        Args:
            file_path: Path to devcontainer.json file
            
        Returns:
            ParseResult containing extracted config or errors
        """
        try:
            path = Path(file_path)
            
            # Check if file exists
            if not path.exists():
                return ParseResult(
                    success=False,
                    errors=[f"File not found: {file_path}"]
                )
            
            # Check if file is readable
            if not path.is_file():
                return ParseResult(
                    success=False,
                    errors=[f"Path is not a file: {file_path}"]
                )
            
            # Read file content
            try:
                content = path.read_text(encoding='utf-8')
            except PermissionError:
                return ParseResult(
                    success=False,
                    errors=[f"Permission denied reading {file_path}"]
                )
            except Exception as e:
                return ParseResult(
                    success=False,
                    errors=[f"Error reading file {file_path}: {str(e)}"]
                )
            
            # Parse the content
            return self.parse_content(content)
            
        except Exception as e:
            return ParseResult(
                success=False,
                errors=[f"Unexpected error parsing file: {str(e)}"]
            )
    
    def parse_content(self, content: str) -> ParseResult:
        """
        Parse devcontainer.json content from string.
        
        Args:
            content: JSON string content
            
        Returns:
            ParseResult containing extracted config or errors
        """
        try:
            # Parse JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                return ParseResult(
                    success=False,
                    errors=[f"Invalid JSON syntax at line {e.lineno}, column {e.colno}: {e.msg}"]
                )
            
            # Validate it's a dictionary
            if not isinstance(data, dict):
                return ParseResult(
                    success=False,
                    errors=["Invalid devcontainer.json: root must be an object"]
                )
            
            # Validate schema
            schema_errors = self.validate_schema(data)
            if schema_errors:
                return ParseResult(
                    success=False,
                    errors=schema_errors
                )
            
            # Extract configuration using dedicated extraction methods
            image, dockerfile = self._extract_image_config(data)
            config = DevcontainerConfig(
                features=self._extract_features(data),
                customizations=self._extract_customizations(data),
                forward_ports=self._extract_ports(data.get('forwardPorts', [])),
                remote_env=self._extract_env(data),
                image=image,
                dockerfile=dockerfile,
                raw=data
            )
            
            return ParseResult(
                success=True,
                config=config,
                errors=[]
            )
            
        except Exception as e:
            return ParseResult(
                success=False,
                errors=[f"Unexpected error parsing content: {str(e)}"]
            )
    
    def validate_schema(self, data: dict) -> list[str]:
        """
        Validate devcontainer.json against schema.
        
        Args:
            data: Parsed JSON dictionary
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # If jsonschema is available, use it for validation
        if validate is not None and ValidationError is not None:
            try:
                validate(instance=data, schema=self.DEVCONTAINER_SCHEMA)
            except ValidationError as e:
                # Format validation error message
                path = '.'.join(str(p) for p in e.path) if e.path else 'root'
                errors.append(f"Schema validation failed at '{path}': {e.message}")
            except Exception as e:
                errors.append(f"Schema validation error: {str(e)}")
        else:
            # Basic validation without jsonschema
            errors.extend(self._basic_validation(data))
        
        return errors
    
    def _basic_validation(self, data: dict) -> list[str]:
        """
        Perform basic validation when jsonschema is not available.
        
        Checks that known top-level properties have the correct types.
        This is a lightweight fallback used only when the jsonschema
        library is not installed.
        
        Args:
            data: Parsed JSON dictionary
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Check features is a dict if present
        if 'features' in data and not isinstance(data['features'], dict):
            errors.append("Property 'features' must be an object")
        
        # Check customizations is a dict if present
        if 'customizations' in data and not isinstance(data['customizations'], dict):
            errors.append("Property 'customizations' must be an object")
        
        # Check forwardPorts is a list if present
        if 'forwardPorts' in data and not isinstance(data['forwardPorts'], list):
            errors.append("Property 'forwardPorts' must be an array")
        
        # Check remoteEnv is a dict if present
        if 'remoteEnv' in data and not isinstance(data['remoteEnv'], dict):
            errors.append("Property 'remoteEnv' must be an object")
        
        # Check image is a string if present
        if 'image' in data and not isinstance(data['image'], str):
            errors.append("Property 'image' must be a string")
        
        # Check dockerfile is a string if present
        if 'dockerfile' in data and not isinstance(data['dockerfile'], str):
            errors.append("Property 'dockerfile' must be a string")
        
        return errors
    def _extract_features(self, data: dict) -> dict[str, Any]:
        """
        Extract features property from parsed devcontainer data.

        Args:
            data: Parsed JSON dictionary

        Returns:
            Dictionary of features (empty dict if not present)
        """
        features = data.get('features', {})
        if not isinstance(features, dict):
            return {}
        return features

    def _extract_customizations(self, data: dict) -> dict[str, Any]:
        """
        Extract customizations property from parsed devcontainer data.

        Args:
            data: Parsed JSON dictionary

        Returns:
            Dictionary of customizations (empty dict if not present)
        """
        customizations = data.get('customizations', {})
        if not isinstance(customizations, dict):
            return {}
        return customizations

    def _extract_env(self, data: dict) -> dict[str, str]:
        """
        Extract remoteEnv variables from parsed devcontainer data.

        Args:
            data: Parsed JSON dictionary

        Returns:
            Dictionary of environment variable key-value pairs
        """
        remote_env = data.get('remoteEnv', {})
        if not isinstance(remote_env, dict):
            return {}
        # Filter to only string values
        return {k: v for k, v in remote_env.items() if isinstance(v, str)}

    def _extract_image_config(self, data: dict) -> tuple[Optional[str], Optional[str]]:
        """
        Extract image and dockerfile from parsed devcontainer data.

        Args:
            data: Parsed JSON dictionary

        Returns:
            Tuple of (image, dockerfile) - either or both may be None
        """
        image = data.get('image')
        if not isinstance(image, str):
            image = None

        dockerfile = data.get('dockerfile')
        if not isinstance(dockerfile, str):
            dockerfile = None

        return image, dockerfile
    
    def _extract_ports(self, ports_data: list) -> list[int]:
        """
        Extract and normalize port numbers from forwardPorts.
        
        Args:
            ports_data: List of port numbers (can be int or string)
            
        Returns:
            List of integer port numbers
        """
        ports = []
        for port in ports_data:
            try:
                # Convert to int if it's a string
                if isinstance(port, str):
                    port = int(port)
                if isinstance(port, int):
                    ports.append(port)
            except (ValueError, TypeError):
                # Skip invalid port values
                continue
        return ports
