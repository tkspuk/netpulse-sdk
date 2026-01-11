"""
Type aliases for NetPulse SDK

This module provides type aliases for commonly used types across the SDK.
"""

from typing import Dict, List, Union

# Device specification types
DeviceSpec = Union[str, Dict[str, str]]
"""A device can be specified as a string (hostname/IP) or a dict with connection details."""

DeviceList = Union[DeviceSpec, List[DeviceSpec]]
"""A single device or a list of devices."""

# Command specification types
CommandSpec = Union[str, List[str]]
"""A command can be a single string or a list of strings."""

# Configuration types
ConnectionArgs = Dict[str, str]
"""Connection arguments dictionary (username, password, device_type, etc.)."""

DriverArgs = Dict[str, Union[str, int, float, bool]]
"""Driver-specific arguments dictionary."""

WebhookConfig = Dict[str, Union[str, int, Dict[str, str]]]
"""Webhook callback configuration."""

CredentialConfig = Dict[str, Union[str, Dict[str, str]]]
"""Vault credential configuration."""

RenderingConfig = Dict[str, Union[str, Dict[str, str]]]
"""Template rendering configuration."""

ParsingConfig = Dict[str, Union[str, Dict[str, str]]]
"""Output parsing configuration."""
