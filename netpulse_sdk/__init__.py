"""
NetPulse SDK - Python client for NetPulse Network Automation Platform
"""

from importlib.metadata import version, PackageNotFoundError

from .client import NetPulseClient
from .enums import DriverName, JobStatus, QueueStrategy, TaskStatus
from .error import (
    AuthError,
    Error,
    JobFailedError,
    NetPulseError,
    NetworkError,
    RequestTimeoutError,
    TimeoutError,
)
from .job import Job, JobGroup
from .result import ConnectionTestResult, DetachedTaskInfo, JobProgress, Result, WorkerInfo
from .types import (
    CommandSpec,
    ConnectionArgs,
    CredentialConfig,
    DeviceList,
    DeviceSpec,
    DriverArgs,
    FileTransferConfig,
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
    "JobStatus",
    "TaskStatus",
    # Job and Results
    "Job",
    "JobGroup",
    "Result",
    "JobProgress",
    "ConnectionTestResult",
    "WorkerInfo",
    "DetachedTaskInfo",
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
    "FileTransferConfig",
    "WebhookConfig",
    "CredentialConfig",
    "RenderingConfig",
    "ParsingConfig",
    # Utilities
    "setup_logging",
    "enable_debug",
]
