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
    # Paramiko-specific
    pkey: str
    """Raw SSH private key content (PEM string). Alternative to key_file."""
    passphrase: str
    """Passphrase for the private key."""
    keepalive: int
    """Seconds between SSH keepalive packets. Enables persistent connection pooling."""
    host_key_policy: str
    """SSH host key policy: 'auto_add' (default), 'reject', or 'warning'."""
    proxy_host: str
    """Jump host address for tunnelled connections."""
    proxy_port: int
    """Jump host SSH port (default 22)."""
    proxy_username: str
    """Jump host username."""
    proxy_password: str
    """Jump host password."""
    proxy_pkey: str
    """Raw private key content for the jump host."""
    proxy_key_filename: str
    """Path to the jump host's SSH private key file."""
    timeout: float
    """SSH connection timeout in seconds (default 30.0). Separate from per-command read_timeout."""
    compress: bool
    """Enable SSH compression."""
    look_for_keys: bool
    """Automatically search for private key files in ~/.ssh/ (default True)."""
    allow_agent: bool
    """Allow SSH agent for authentication (default False)."""


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


class NetmikoDriverArgs(DriverArgs, total=False):
    """Netmiko-specific driver arguments (SSH to network devices).

    Extends DriverArgs with Netmiko-only options for fine-tuning CLI interaction.
    """

    strip_prompt: bool
    """Remove device prompt from output (default True in Netmiko)."""
    strip_command: bool
    """Remove the command echo from output (default True in Netmiko)."""
    normalize: bool
    """Normalize line endings in output."""
    use_textfsm: bool
    """Parse output with TextFSM (requires NTC templates installed on server)."""
    expect_string: str
    """Custom expect string to wait for instead of the prompt."""
    auto_find_prompt: bool
    """Automatically discover the device prompt."""
    banner_timeout: float
    """Timeout waiting for the SSH banner."""
    conn_timeout: float
    """TCP connection timeout in seconds."""
    auth_timeout: float
    """SSH authentication timeout in seconds."""


class ParamikoDriverArgs(DriverArgs, total=False):
    """Paramiko-specific driver arguments (SSH to Linux/Unix servers).

    Extends DriverArgs with Paramiko-only options for shell interaction.
    """

    sudo: bool
    """Run command with sudo."""
    sudo_password: str
    """Password for sudo (if required and different from login password)."""
    expect_map: Dict[str, str]
    """Interactive prompt → response mapping.
    Example: {"Are you sure?": "yes", "Password:": "secret"}
    """
    working_directory: str
    """Change to this directory before executing the command."""
    environment: Dict[str, str]
    """Environment variables to set for the command.
    Example: {"PATH": "/usr/local/bin:/usr/bin", "DEBUG": "1"}
    """
    get_pty: bool
    """Request a pseudo-TTY. Required for interactive programs (top, passwd, etc.)."""
    script_content: str
    """Inline script body to execute directly, without uploading a file first."""
    script_interpreter: str
    """Interpreter for script_content: 'bash' (default), 'sh', 'python3', etc."""
    stop_on_error: bool
    """Config mode: stop subsequent commands after the first failure (default True)."""
    invoke_shell: bool
    """Use an interactive shell channel instead of exec_command."""
    banner_timeout: float
    """Timeout waiting for the SSH banner."""
    auth_timeout: float
    """SSH authentication timeout in seconds."""


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

    name: str  # Name of the WebHookCaller
    url: str  # Webhook URL (Required if using webhook)
    method: str  # GET, POST, PUT, DELETE, PATCH
    headers: Dict[str, str]
    cookies: Dict[str, str]
    auth: tuple  # (Username, Password) for Basic Auth
    timeout: float


class CredentialConfig(TypedDict, total=False):
    """Vault credential configuration."""

    name: str  # Credential provider name
    ref: str  # Provider-specific reference (e.g., secret path or ID) (Required)
    mount: str
    version: int
    field_mapping: Dict[str, str]
    namespace: str


class RenderingConfig(TypedDict, total=False):
    """Template rendering configuration."""

    name: str  # Renderer engine name, optional, defaults to 'jinja2' in API
    template: str  # Jinja2 template string (either template or template_id is required)
    template_id: str
    format: str


class ParsingConfig(TypedDict, total=False):
    """Output parsing configuration."""

    name: str  # Parser engine name, optional, defaults to 'textfsm' in API
    template: str  # Parsing template string (either template or template_id is required)
    template_id: str
    format: str
