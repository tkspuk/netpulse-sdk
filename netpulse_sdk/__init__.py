"""
NetPulse SDK - Python client for NetPulse Network Automation Platform
"""

from .client import NetPulseClient
from .error import AuthError, Error, JobFailedError, NetPulseError, NetworkError, TimeoutError
from .job import Job
from .result import JobProgress, Result
from .utils import setup_logging

# 保持向后兼容，导出为 NetPulse
NetPulse = NetPulseClient

__version__ = "netpulse-sdk"

__all__ = [
    "NetPulse",
    "Job",
    "Result",
    "JobProgress",
    "NetPulseError",
    "AuthError",
    "NetworkError",
    "TimeoutError",
    "JobFailedError",
    "Error",
    "setup_logging",
]
