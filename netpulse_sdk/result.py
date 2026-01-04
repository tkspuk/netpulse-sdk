"""
Result and JobProgress data models
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from .error import Error


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
    error: Optional[Error] = Field(default=None, description="Error information")

    def has_device_error(self, patterns: Optional[List[str]] = None) -> bool:
        """Check if device output contains error indicators

        Args:
            patterns: List of error patterns to check. Defaults to common patterns.

        Returns:
            True if any error pattern is found in stdout, False otherwise.
        """
        default_patterns = [
            "Error:",
            "% Error",
            "Invalid",
            "Failed",
            "Incomplete",
            "Unrecognized",
            "not found",
            "% ",
            "^",
            "Too many parameters",
            "Unknown command",
            "Syntax error",
            "Bad IP address",
            "Ambiguous command",
        ]
        patterns = patterns or default_patterns

        if not self.ok:
            return True

        stdout_lower = self.stdout.lower()
        return any(pattern.lower() in stdout_lower for pattern in patterns)

    @property
    def is_success(self) -> bool:
        """True success: task completed AND device returned no errors"""
        return self.ok and not self.has_device_error()

    def get_error_lines(self) -> List[str]:
        """Extract error lines from output

        Returns:
            List of lines containing error indicators
        """
        if not self.stdout:
            return []

        error_lines = []
        for line in self.stdout.split("\n"):
            line_lower = line.lower()
            if any(pattern in line_lower for pattern in ["error", "invalid", "failed", "%", "^"]):
                error_lines.append(line.strip())

        return error_lines

    def __repr__(self):
        status = "OK" if self.ok else "FAILED"
        return f"Result({self.device_name}:{self.command} [{status}])"
