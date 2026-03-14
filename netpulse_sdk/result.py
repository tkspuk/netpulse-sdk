"""
Result and JobProgress data models
"""

import re
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .error import Error

# Shared error patterns for device output detection.
# Each pattern is a regex matched per-line (case-insensitive).
# Use line-start anchors where appropriate to reduce false positives.
DEFAULT_DEVICE_ERROR_PATTERNS = [
    r"^% ",                # Cisco/Arista CLI error prefix
    r"^%\S",               # Cisco CLI error (no space after %)
    r"Error:",             # Explicit error label
    r"Invalid input",      # Command syntax error
    r"Incomplete command",  # Missing required arguments
    r"Unrecognized command",
    r"Unknown command",
    r"Syntax error",
    r"Bad IP address",
    r"Ambiguous command",
    r"Too many parameters",
]


class WorkerInfo(BaseModel):
    """Worker status information (mirrors backend WorkerInResponse)"""

    name: str = Field(..., description="Worker name")
    status: str = Field(..., description="Worker status: idle, busy, suspended")
    pid: Optional[int] = Field(default=None, description="Process ID")
    hostname: Optional[str] = Field(default=None, description="Host name")
    queues: Optional[List[str]] = Field(default=None, description="Queue names")
    last_heartbeat: Optional[str] = Field(default=None, description="Last heartbeat time")
    birth_at: Optional[str] = Field(default=None, description="Worker start time")
    successful_job_count: Optional[int] = Field(default=None, description="Successful job count")
    failed_job_count: Optional[int] = Field(default=None, description="Failed job count")

    model_config = ConfigDict(extra="allow")

    def __repr__(self):
        return f"WorkerInfo({self.name} [{self.status}])"


class DetachedTaskInfo(BaseModel):
    """Detached task metadata (mirrors backend DetachedTaskInResponse)"""

    task_id: str = Field(..., description="Detached task ID")
    command: List[str] = Field(default_factory=list, description="Command list")
    host: str = Field(..., description="Device IP/hostname")
    driver: str = Field(..., description="Driver name")
    status: str = Field(..., description="Task status: running, completed, launching")
    last_sync: Optional[str] = Field(default=None, description="Last sync time")
    created_at: Optional[str] = Field(default=None, description="Creation time")
    push_interval: Optional[int] = Field(default=None, description="Webhook push interval")
    last_offset: Optional[int] = Field(default=None, description="Last log byte offset")
    connection_args: Optional[dict] = Field(default=None, description="Connection args (masked)")

    model_config = ConfigDict(extra="allow")

    def __repr__(self):
        return f"DetachedTaskInfo({self.task_id} @ {self.host} [{self.status}])"


class ConnectionTestResult(BaseModel):
    """Device connection test result"""

    ok: bool = Field(..., description="Whether connection test succeeded")
    host: str = Field(..., description="Device IP/hostname")
    latency: Optional[float] = Field(default=None, description="Connection latency in seconds")
    duration_ms: int = Field(default=0, description="Duration in milliseconds")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    driver: str = Field(..., description="Driver used for testing")
    timestamp: Optional[datetime] = Field(default=None, description="Test timestamp")

    # Extra fields for specific drivers
    remote_version: Optional[str] = Field(
        default=None, description="Remote system version (Paramiko)"
    )
    prompt: Optional[str] = Field(default=None, description="Device prompt (Netmiko)")
    device_type: Optional[str] = Field(default=None, description="Actual device type detected")

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return self.model_dump(by_alias=False)

    def __repr__(self):
        status = "OK" if self.ok else "FAILED"
        dur_str = f" {self.duration_ms}ms" if self.duration_ms else ""
        return f"ConnectionTestResult({self.host} [{status}]{dur_str})"


class JobProgress(BaseModel):
    """Job execution progress"""

    total: int = Field(..., description="Total execution units (device × command)")
    completed: int = Field(default=0, description="Completed execution units")
    failed: int = Field(default=0, description="Failed execution units")
    running: int = Field(default=0, description="Running/queued execution units")

    @property
    def percentage(self) -> float:
        """Completion percentage"""
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100


class Result(BaseModel):
    """Standardized execution result"""

    job_id: str = Field(..., description="Job ID")
    device_id: str = Field(..., description="Device IP/identifier")
    device_name: str = Field(..., description="Device name")
    command: str = Field(..., description="Executed command")
    stdout: str = Field(default="", description="Standard output")
    stderr: str = Field(default="", description="Standard error")
    ok: bool = Field(..., description="Whether execution succeeded")
    duration_ms: int = Field(default=0, description="Execution duration in milliseconds")
    exit_status: int = Field(default=0, description="Command exit status")
    download_url: Optional[str] = Field(default=None, description="Download URL for files")
    metadata: dict = Field(default_factory=dict, description="Execution metadata")
    parsed: Optional[Any] = Field(default=None, description="Parsed structured data")
    error: Optional[Error] = Field(default=None, description="Error information")

    def has_device_error(self, patterns: Optional[List[str]] = None) -> bool:
        """Check if device output contains error indicators

        Uses per-line regex matching to reduce false positives.

        Args:
            patterns: List of regex patterns to check (case-insensitive, matched per line).
                Defaults to DEFAULT_DEVICE_ERROR_PATTERNS.

        Returns:
            True if any error pattern is found in stdout, False otherwise.
        """
        if not self.ok:
            return True

        if not self.stdout:
            return False

        check_patterns = patterns or DEFAULT_DEVICE_ERROR_PATTERNS
        compiled = [re.compile(p, re.IGNORECASE) for p in check_patterns]

        for line in self.stdout.split("\n"):
            if any(pat.search(line) for pat in compiled):
                return True
        return False

    @property
    def is_success(self) -> bool:
        """True success: task completed AND device returned no errors"""
        return self.ok and not self.has_device_error()

    @property
    def duration_s(self) -> float:
        """Execution duration in seconds (convenience for duration_ms)"""
        return self.duration_ms / 1000.0

    def __bool__(self) -> bool:
        """Allow natural truthiness: `if result:` returns True when ok"""
        return self.ok

    def get_error_lines(self, patterns: Optional[List[str]] = None) -> List[str]:
        """Extract error lines from output

        Uses the same patterns as has_device_error() for consistency.

        Args:
            patterns: List of regex patterns (case-insensitive, matched per line).
                Defaults to DEFAULT_DEVICE_ERROR_PATTERNS.

        Returns:
            List of lines containing error indicators
        """
        if not self.stdout:
            return []

        check_patterns = patterns or DEFAULT_DEVICE_ERROR_PATTERNS
        compiled = [re.compile(p, re.IGNORECASE) for p in check_patterns]

        error_lines = []
        for line in self.stdout.split("\n"):
            if any(pat.search(line) for pat in compiled):
                error_lines.append(line.strip())

        return error_lines

    def to_dict(self) -> dict:
        """Convert to dictionary for easy serialization"""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert to JSON string"""
        return self.model_dump_json(indent=2)

    def __repr__(self):
        status = "OK" if self.ok else "FAILED"
        dur = f" {self.duration_ms}ms" if self.duration_ms else ""
        return f"Result({self.device_name}:{self.command} [{status}]{dur})"
