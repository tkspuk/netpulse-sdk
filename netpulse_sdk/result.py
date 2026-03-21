"""
Result and JobProgress data models
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .error import Error

# Shared error patterns for device output detection.
# Each pattern is a regex matched per-line (case-insensitive).
# Use line-start anchors where appropriate to reduce false positives.
DEFAULT_DEVICE_ERROR_PATTERNS = [
    r"^% ",  # Cisco/Arista CLI error prefix
    r"^%\S",  # Cisco CLI error (no space after %)
    r"Error:",  # Explicit error label
    r"Invalid input",  # Command syntax error
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


class DetachedTaskLog(BaseModel):
    """Response from GET /detached-tasks/{task_id} — log snapshot with metadata"""

    task_id: str = Field(..., description="Detached task ID")
    output: str = Field(default="", description="Log output since last offset")
    is_running: bool = Field(default=False, description="Whether the process is still alive")
    next_offset: int = Field(
        default=0, description="Pass as ?offset= in the next call for incremental reading"
    )
    completed: bool = Field(default=False, description="Whether the task has completed")
    pid: Optional[int] = Field(default=None, description="Remote process PID")

    model_config = ConfigDict(extra="allow")

    def __repr__(self):
        state = "running" if self.is_running else "done"
        return f"DetachedTaskLog({self.task_id} [{state}], offset={self.next_offset})"


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


class WebhookEvent(BaseModel):
    """Webhook event payload received from NetPulse server.

    Use this model to parse incoming webhook HTTP request bodies::

        event = WebhookEvent.model_validate(request.json())

        if event.final:
            # One-shot task or detached task completed
            for item in (event.result or {}).get("retval") or []:
                print(item["stdout"])
        else:
            # Incremental log push from detached task
            buffer.append(event.result)

    Attributes:
        id: Job ID or Task ID (for detached tasks).
        status: Job status aligned with API (``"finished"``, ``"failed"``).
        event_type: Event classification — ``"job.completed"``, ``"job.failed"``,
            ``"detached.completed"``, ``"detached.failed"``, ``"detached.log_push"``.
        final: ``True`` if no more events will follow for this ID.
        timestamp: ISO 8601 timestamp of when the webhook was generated.
        result: Structured result dict with ``type`` (string), ``retval`` (list), ``error``.
        device: Device connection info (``host``, ``device_type``).
    """

    id: str = Field(..., description="Job ID or Task ID")
    status: str = Field(..., description="Job status: finished, failed, etc.")
    event_type: str = Field(..., description="Event type: job.completed, detached.log_push, etc.")
    final: bool = Field(..., description="True if no more events will follow for this ID")
    timestamp: str = Field(..., description="ISO 8601 timestamp of webhook generation")
    started_at: Optional[str] = Field(default=None, description="Job execution start time")
    ended_at: Optional[str] = Field(default=None, description="Job execution end time")
    duration: Optional[float] = Field(default=None, description="Execution duration in seconds")
    result: Optional[dict] = Field(default=None, description="Structured result (type, retval, error)")
    device: Optional[Dict[str, str]] = Field(default=None, description="Device info (host, device_type)")
    task_id: Optional[str] = Field(default=None, description="Detached task ID")
    device_name: Optional[str] = Field(default=None, description="Human-readable device name")
    command: Optional[List[str]] = Field(default=None, description="List of executed commands")

    model_config = ConfigDict(extra="allow")

    @property
    def ok(self) -> bool:
        """True if the event indicates success."""
        return self.event_type in ("job.completed", "detached.completed", "detached.log_push")

    @property
    def retval(self) -> list:
        """Shortcut to result.retval (list of DriverExecutionResult dicts)."""
        if self.result:
            return self.result.get("retval") or []
        return []

    @property
    def error(self) -> Optional[dict]:
        """Shortcut to result.error dict (has 'type' and 'message' keys)."""
        if self.result:
            return self.result.get("error")
        return None

    def __repr__(self):
        final_str = " FINAL" if self.final else ""
        return f"WebhookEvent({self.event_type}{final_str} id={self.id})"
