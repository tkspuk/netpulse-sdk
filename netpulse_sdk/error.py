"""
NetPulse SDK error classes
"""

from typing import Optional

from pydantic import BaseModel


class NetPulseError(Exception):
    """Base SDK error"""

    def __init__(self, message: str, detail: Optional[dict] = None):
        self.message = message
        self.detail = detail or {}
        super().__init__(message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, detail={self.detail})"

    def __str__(self) -> str:
        return self.message


class AuthError(NetPulseError):
    """API key authentication failed"""

    def __init__(
        self, message: str = "API key authentication failed", detail: Optional[dict] = None
    ):
        super().__init__(message, detail)


class NetworkError(NetPulseError):
    """Network request failed (retryable)"""

    def __init__(self, message: str, detail: Optional[dict] = None):
        super().__init__(message, detail)


class RequestTimeoutError(NetPulseError):
    """Request timeout"""

    def __init__(self, message: str, url: Optional[str] = None, detail: Optional[dict] = None):
        self.url = url
        if detail is None:
            detail = {}
        if url:
            detail["url"] = url
        super().__init__(message, detail)


# Backward compatibility alias
TimeoutError = RequestTimeoutError


class JobFailedError(NetPulseError):
    """Job execution failed"""

    def __init__(self, message: str, job_id: Optional[str] = None, detail: Optional[dict] = None):
        self.job_id = job_id
        if detail is None:
            detail = {}
        if job_id:
            detail["job_id"] = job_id
        super().__init__(message, detail)


class Error(BaseModel):
    """Error information in Result"""

    type: str
    message: str
    retryable: bool = False

    def __repr__(self):
        return f"Error(type={self.type}, message={self.message}, retryable={self.retryable})"
