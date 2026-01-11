"""
NetPulse SDK - Python client for NetPulse Network Automation Platform
"""

from importlib.metadata import version, PackageNotFoundError

from .client import NetPulseClient
from .enums import DriverName, QueueStrategy
from .error import (
    AuthError,
    Error,
    JobFailedError,
    NetPulseError,
    NetworkError,
    RequestTimeoutError,
    TimeoutError,
)
from .job import Job
from .result import ConnectionTestResult, JobProgress, Result
from .types import (
    CommandSpec,
    ConnectionArgs,
    CredentialConfig,
    DeviceList,
    DeviceSpec,
    DriverArgs,
    ParsingConfig,
    RenderingConfig,
    WebhookConfig,
)
from .utils import setup_logging, enable_debug

# 保持向后兼容，导出为 NetPulse
NetPulse = NetPulseClient

try:
    __version__ = version("netpulse-sdk")
except PackageNotFoundError:
    __version__ = "dev"  # Fallback when package is not installed

__all__ = [
    # Client
    "NetPulseClient",
    "NetPulse",
    # Enums
    "DriverName",
    "QueueStrategy",
    # Job and Results
    "Job",
    "Result",
    "JobProgress",
    "ConnectionTestResult",
    # Errors
    "NetPulseError",
    "AuthError",
    "NetworkError",
    "RequestTimeoutError",
    "TimeoutError",
    "JobFailedError",
    "Error",
    # Type aliases
    "DeviceSpec",
    "DeviceList",
    "CommandSpec",
    "ConnectionArgs",
    "DriverArgs",
    "WebhookConfig",
    "CredentialConfig",
    "RenderingConfig",
    "ParsingConfig",
    # Utilities
    "setup_logging",
    "enable_debug",
]
