"""
Type aliases for NetPulse SDK

This module provides type aliases for commonly used types across the SDK.
"""

from typing import Dict, List, Union, TypedDict
from typing_extensions import NotRequired

# Device specification types
DeviceSpec = Union[str, Dict[str, str]]
"""A device can be specified as a string (hostname/IP) or a dict with connection details."""

DeviceList = Union[DeviceSpec, List[DeviceSpec]]
"""A single device or a list of devices."""

# Command specification types
CommandSpec = Union[str, List[str]]
"""A command can be a single string or a list of strings."""

# Typed Configuration Dictionaries (for enhanced IDE support)
class ConnectionArgs(TypedDict, total=False):
    """Connection arguments dictionary."""
    host: str
    device_type: str
    username: str
    password: str
    port: int
    secret: str
    key_file: str

class DriverArgs(TypedDict, total=False):
    """Driver-specific arguments dictionary. Overrides default driver behaviours."""
    read_timeout: int
    delay_factor: int
    max_loops: int
    cmd_verify: bool
    terminator: str
    timeout: int
    global_delay_factor: float
    session_log: str
    custom_enter: str

class FileTransferConfig(TypedDict, total=False):
    """File transfer configuration."""
    operation: str  # 'upload' or 'download'
    remote_path: str
    local_path: NotRequired[str]
    overwrite: NotRequired[bool]
    resume: NotRequired[bool]
    recursive: NotRequired[bool]
    sync_mode: NotRequired[str]  # 'full' or 'hash'
    hash_algorithm: NotRequired[str]
    verify_file: NotRequired[bool]
    chunk_size: NotRequired[int]
    chmod: NotRequired[str]
    execute_after_upload: NotRequired[bool]
    execute_command: NotRequired[str]
    cleanup_after_exec: NotRequired[bool]

class WebhookConfig(TypedDict, total=False):
    """Webhook callback configuration."""
    name: str # Name of the WebHookCaller
    url: str  # Webhook URL (Required if using webhook)
    method: str # GET, POST, PUT, DELETE, PATCH
    headers: Dict[str, str]
    cookies: Dict[str, str]
    auth: tuple # (Username, Password) for Basic Auth
    timeout: float

class CredentialConfig(TypedDict, total=False):
    """Vault credential configuration."""
    name: str # Credential provider name
    ref: str  # Provider-specific reference (e.g., secret path or ID) (Required)
    mount: str
    version: int
    field_mapping: Dict[str, str]
    namespace: str

class RenderingConfig(TypedDict, total=False):
    """Template rendering configuration."""
    name: str # Renderer engine name, optional, defaults to 'jinja2' in API
    template: str # Jinja2 template string (either template or template_id is required)
    template_id: str
    format: str

class ParsingConfig(TypedDict, total=False):
    """Output parsing configuration."""
    name: str # Parser engine name, optional, defaults to 'textfsm' in API
    template: str # Parsing template string (either template or template_id is required)
    template_id: str
    format: str

