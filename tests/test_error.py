import pytest
from netpulse_sdk.error import (
    NetPulseError,
    AuthError,
    NetworkError,
    RequestTimeoutError,
    JobFailedError,
    Error,
)


class TestErrors:
    def test_netpulse_error_basic(self):
        e = NetPulseError("something failed", detail={"code": 500})
        assert str(e) == "something failed"
        assert e.detail["code"] == 500
        assert "something failed" in repr(e)

    def test_netpulse_error_default_detail(self):
        e = NetPulseError("oops")
        assert e.detail == {}

    def test_auth_error_default_message(self):
        e = AuthError()
        assert "authentication" in str(e).lower()

    def test_auth_error_custom_message(self):
        e = AuthError("bad key", detail={"key": "x"})
        assert str(e) == "bad key"

    def test_network_error(self):
        e = NetworkError("connection reset")
        assert isinstance(e, NetPulseError)
        assert str(e) == "connection reset"

    def test_request_timeout_error_with_url(self):
        e = RequestTimeoutError("timed out", url="http://api/test")
        assert e.url == "http://api/test"
        assert e.detail["url"] == "http://api/test"

    def test_request_timeout_error_without_url(self):
        e = RequestTimeoutError("timed out")
        assert e.url is None
        assert "url" not in e.detail

    def test_job_failed_error_with_job_id(self):
        e = JobFailedError("job blew up", job_id="job-123")
        assert e.job_id == "job-123"
        assert e.detail["job_id"] == "job-123"

    def test_job_failed_error_without_job_id(self):
        e = JobFailedError("generic failure")
        assert e.job_id is None
        assert "job_id" not in e.detail

    def test_error_model_repr(self):
        e = Error(type="timeout", message="device timed out", retryable=True)
        r = repr(e)
        assert "timeout" in r
        assert "retryable=True" in r

    def test_error_is_exception(self):
        with pytest.raises(NetPulseError, match="test"):
            raise NetPulseError("test")
