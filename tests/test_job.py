import pytest
from unittest.mock import patch
from netpulse_sdk import Job
from netpulse_sdk.error import JobFailedError

class TestJob:
    def test_job_refresh_and_done(self, mock_client, sample_job_data):
        # Initial status: started
        data1 = sample_job_data.copy()
        data1["status"] = "started"
        data1["result"] = None
        
        # Finished status
        data2 = sample_job_data.copy()
        
        mock_client._http.get.side_effect = [data2]
        
        job = Job(client=mock_client, job_data=data1, device_name="d1", command=["cmd"])
        assert job.is_done() is False
        
        job.refresh()
        assert job.status == "finished"
        assert job.is_done() is True
        
    def test_job_results_parsing(self, mock_client, sample_job_data):
        job = Job(client=mock_client, job_data=sample_job_data, device_name="d1", command=["cmd"])
        results = job.results()
        
        assert len(results) == 1
        res = results[0]
        assert res.stdout == "Cisco IOS XE Software, Version 17.03.03"
        assert res.parsed["version"] == "17.03.03"
        assert res.ok is True
        
        # Test properties (Now stdout is a string)
        assert res.stdout in job.stdout
        assert job.stdout_dict["show version"] == res.stdout
        assert job.parsed["show version"] == res.parsed

    def test_job_multi_command_properties(self, mock_client):
        # Data with two commands
        data = {
            "id": "j-multi", "status": "finished",
            "result": {
                "type": 1,
                "retval": [
                    {"command": "c1", "stdout": "out1", "parsed": {"v": 1}},
                    {"command": "c2", "stdout": "out2", "parsed": {"v": 2}}
                ]
            },
            "command": ["c1", "c2"]
        }
        job = Job(mock_client, data, "d1", ["c1", "c2"])
        
        # stdout is now a consolidated string for Job
        assert "out1" in job.stdout
        assert "out2" in job.stdout
        
        # Use stdout_dict for command-specific mapping
        assert job.stdout_dict["c1"] == "out1"
        assert job.stdout_dict["c2"] == "out2"
        assert job.parsed["c2"]["v"] == 2

    def test_job_wait_with_backoff(self, mock_client, sample_job_data):
        # Mocking time.sleep to speed up tests
        with patch("time.sleep"):
            data_started = sample_job_data.copy()
            data_started["status"] = "started"
            
            # Return 'started' twice, then 'finished'
            mock_client._http.get.side_effect = [data_started, sample_job_data]
            
            job = Job(client=mock_client, job_data=data_started, device_name="d1", command=["cmd"])
            job.wait(poll_interval=0.1)
            
            assert job.is_done() is True
            assert mock_client._http.get.call_count == 2

    def test_job_getitem_access(self, mock_client, sample_job_data):
        job = Job(client=mock_client, job_data=sample_job_data, device_name="d1", command=["show version"])

        # Access by index (now returns single Result object)
        res = job[0]
        assert res.command == "show version"

        # Access by command pattern
        res_list_pattern = job["version"]
        assert len(res_list_pattern) == 1
        assert "version" in res_list_pattern[0].command

    def test_cancel_survives_404_on_refresh(self, mock_client, sample_job_data):
        """cancel() should not raise if backend deletes the job (404 on refresh)"""
        queued_data = sample_job_data.copy()
        queued_data["status"] = "queued"
        queued_data["result"] = None

        mock_client._http.delete.return_value = None
        mock_client._http.get.side_effect = Exception("404 Not Found")

        job = Job(client=mock_client, job_data=queued_data, device_name="d1", command=["cmd"])
        result = job.cancel()

        assert result is True
        assert job.status == "canceled"

    def test_repr_with_zero_duration(self, mock_client, sample_job_data):
        """__repr__ should display duration even when it is 0.0"""
        data = sample_job_data.copy()
        data["duration"] = 0.0
        job = Job(client=mock_client, job_data=data, device_name="d1", command=["cmd"])
        assert "duration=0.0s" in repr(job)

    def test_cancel_returns_bool(self, mock_client, sample_job_data):
        """JobInterface.cancel() must return bool; non-queued job returns False"""
        data = sample_job_data.copy()  # status=finished
        job = Job(client=mock_client, job_data=data, device_name="d1", command=["cmd"])
        assert job.cancel() is False

    def test_result_type_property(self, mock_client, sample_job_data):
        """result_type exposes API type field (1=Success, 2=Failed, ...)"""
        job = Job(mock_client, sample_job_data, "d1", ["show version"])
        assert job.result_type == 1

    def test_result_type_none_when_no_result(self, mock_client, sample_job_data):
        data = sample_job_data.copy()
        data["result"] = None
        job = Job(mock_client, data, "d1", ["cmd"])
        assert job.result_type is None

    def test_summary_with_duration(self, mock_client, sample_job_data):
        """summary() includes duration when present"""
        data = sample_job_data.copy()
        data["duration"] = 1.5
        job = Job(mock_client, data, "d1", ["show version"])
        s = job.summary()
        assert "1.5s" in s
        assert "ALL OK" in s

    def test_summary_without_duration(self, mock_client, sample_job_data):
        """summary() omits duration when None"""
        job = Job(mock_client, sample_job_data, "d1", ["show version"])
        s = job.summary()
        assert "1 cmd" in s
        assert "in" not in s

    def test_one_raises_on_multiple_results(self, mock_client):
        data = {
            "id": "j-multi", "status": "finished",
            "result": {
                "type": 1,
                "retval": [
                    {"command": "c1", "stdout": "o1", "metadata": {"host": "d1"}},
                    {"command": "c2", "stdout": "o2", "metadata": {"host": "d1"}},
                ],
            },
        }
        job = Job(mock_client, data, "d1", ["c1", "c2"])
        with pytest.raises(ValueError, match="Expected exactly 1"):
            job.one()

    def test_raise_on_error_passes_when_all_ok(self, mock_client, sample_job_data):
        job = Job(mock_client, sample_job_data, "d1", ["show version"])
        returned = job.raise_on_error()
        assert returned is job  # chaining

    def test_raise_on_error_raises_when_failed(self, mock_client):
        data = {
            "id": "j-fail", "status": "failed",
            "result": {
                "type": 2,
                "retval": [],
                "error": {"type": "connection", "message": "timeout"},
            },
        }
        job = Job(mock_client, data, "d1", ["cmd"])
        with pytest.raises(JobFailedError):
            job.raise_on_error()

    def test_text_property(self, mock_client, sample_job_data):
        """text property formats output with command header"""
        job = Job(mock_client, sample_job_data, "d1", ["show version"])
        t = job.text
        assert "--- show version ---" in t
        assert "Cisco" in t

    def test_failed_commands_property(self, mock_client):
        data = {
            "id": "j1", "status": "finished",
            "result": {
                "type": 1,
                "retval": [
                    {"command": "c1", "stdout": "ok", "exit_status": 0, "metadata": {"host": "d1"}},
                    {"command": "c2", "stdout": "", "exit_status": 1, "metadata": {"host": "d1"}},
                ],
            },
        }
        job = Job(mock_client, data, "d1", ["c1", "c2"])
        assert job.failed_commands == ["c2"]

    def test_job_with_error_result_creates_fallback(self, mock_client):
        """Job with empty retval and error creates a synthetic failed Result"""
        data = {
            "id": "j-err", "status": "failed",
            "result": {
                "type": 2,
                "retval": [],
                "error": {"type": "timeout", "message": "Device timed out"},
            },
        }
        job = Job(mock_client, data, "d1", ["show ver"])
        results = job.results()
        assert len(results) == 1
        assert results[0].ok is False
        assert results[0].error.message == "Device timed out"
        assert results[0].error.retryable is True  # timeout is retryable
