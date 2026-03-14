import pytest
from unittest.mock import patch, MagicMock
from netpulse_sdk import NetPulseClient, Job
from netpulse_sdk.error import NetPulseError
from netpulse_sdk.result import ConnectionTestResult, WorkerInfo, DetachedTaskInfo, DetachedTaskLog

class TestNetPulseClient:
    def test_client_initialization(self):
        client = NetPulseClient(base_url="http://test", api_key="abc")
        assert client._http.base_url == "http://test"
        assert client._http.session.headers["X-API-KEY"] == "abc"

    def test_test_connection_success(self, mock_client):
        # Mock connection test response
        mock_client._http.post.return_value = {
            "success": True,
            "latency": 0.045,
            "error": None,
            "timestamp": "2024-02-24T12:00:00Z",
            "remote_version": "1.0",
            "device_type": "cisco_ios"
        }
        
        res = mock_client.test_connection("10.0.0.1")
        
        assert isinstance(res, ConnectionTestResult)
        assert res.ok is True
        assert res.latency == 0.045
        assert res.remote_version == "1.0"
        mock_client._http.post.assert_called_once()

    def test_run_exec_mode(self, mock_client, sample_job_data):
        # Mock execution response
        mock_client._http.post.return_value = sample_job_data
        
        job = mock_client.run(devices="10.0.0.1", command="show version")
        
        assert isinstance(job, Job)
        assert job.id == "job-123"
        assert job.device_name == "10.0.0.1"
        
        # Verify payload construction
        call_args = mock_client._http.post.call_args[1]
        assert call_args["json"]["command"] == ["show version"]
        assert call_args["json"]["connection_args"]["host"] == "10.0.0.1"

    def test_run_bulk_mode(self, mock_client):
        # Mock bulk execution response
        mock_client._http.post.return_value = {
            "succeeded": [
                {"id": "j1", "status": "queued", "connection_args": {"host": "d1"}},
                {"id": "j2", "status": "queued", "connection_args": {"host": "d2"}}
            ],
            "failed": []
        }
        
        from unittest.mock import ANY
        group = mock_client.run(devices=["d1", "d2"], command="show clock")
        
        assert len(group) == 2
        assert group.jobs[0].id == "j1"
        assert group.jobs[1].id == "j2"
        mock_client._http.post.assert_called_with("/device/bulk", json=ANY)

    def test_get_job(self, mock_client, sample_job_data):
        mock_client._http.get.return_value = sample_job_data
        job = mock_client.get_job("job-123")
        assert job.id == "job-123"
        assert job.status == "finished"

    def test_test_connections_fault_tolerance(self, mock_client):
        """Test that test_connections continues even if one call crashes"""
        def problematic_test(device, **kwargs):
            if device == "broken":
                raise RuntimeError("Driver crash")
            from netpulse_sdk.result import ConnectionTestResult
            return ConnectionTestResult(ok=True, host=device, driver="test")

        # Mock test_connection (the single-device method)
        with patch.object(NetPulseClient, 'test_connection', side_effect=problematic_test):
            results = mock_client.test_connections(["works", "broken", "also_works"])
            
            assert len(results) == 3
            assert results[0].ok is True
            assert results[1].ok is False
            assert "Driver crash" in results[1].error
            assert results[2].ok is True
            assert results[2].host == "also_works" # Verify order is maintained

    def test_collect_rejects_save(self, mock_client, sample_job_data):
        """collect() must refuse save=True"""
        with pytest.raises(ValueError, match="read-only"):
            mock_client.collect("10.0.0.1", command="show ver", save=True)

    def test_collect_rejects_upload(self, mock_client):
        """collect() must refuse file upload"""
        with pytest.raises(ValueError, match="read-only"):
            mock_client.collect(
                "10.0.0.1",
                file_transfer={"operation": "upload", "remote_path": "/tmp/x"},
            )

    def test_collect_requires_command(self, mock_client):
        """collect() without command or file_transfer raises ValueError"""
        with pytest.raises(ValueError, match="requires a command"):
            mock_client.collect("10.0.0.1")

    def test_cancel_job(self, mock_client):
        mock_client._http.delete.return_value = None
        assert mock_client.cancel_job("job-999") is True
        mock_client._http.delete.assert_called_once_with("/jobs/job-999")

    def test_list_workers(self, mock_client):
        mock_client._http.get.return_value = [
            {"name": "worker-1", "status": "idle", "pid": 1234},
            {"name": "worker-2", "status": "busy"},
        ]
        workers = mock_client.list_workers()
        assert len(workers) == 2
        assert isinstance(workers[0], WorkerInfo)
        assert workers[0].name == "worker-1"
        assert workers[0].status == "idle"

    def test_list_detached_tasks(self, mock_client):
        mock_client._http.get.return_value = [
            {
                "task_id": "t-abc",
                "status": "running",
                "command": ["top"],
                "driver": "paramiko",
                "host": "10.0.0.5",
            }
        ]
        tasks = mock_client.list_detached_tasks()
        assert len(tasks) == 1
        assert isinstance(tasks[0], DetachedTaskInfo)
        assert tasks[0].task_id == "t-abc"

    def test_get_detached_task_returns_model(self, mock_client):
        mock_client._http.get.return_value = {
            "task_id": "t-abc",
            "output": "line1\nline2\n",
            "is_running": True,
            "next_offset": 14,
            "completed": False,
            "pid": 5678,
        }
        snap = mock_client.get_detached_task("t-abc", offset=0)
        assert isinstance(snap, DetachedTaskLog)
        assert snap.is_running is True
        assert snap.next_offset == 14
        assert snap.pid == 5678

    def test_tail_detached_task_collects_output(self, mock_client):
        """tail_detached_task loops until is_running=False, collecting output"""
        responses = [
            {"task_id": "t1", "output": "chunk1\n", "is_running": True, "next_offset": 7, "completed": False},
            {"task_id": "t1", "output": "chunk2\n", "is_running": False, "next_offset": 14, "completed": True},
        ]
        mock_client._http.get.side_effect = responses

        with patch("time.sleep"):
            full = mock_client.tail_detached_task("t1", poll_interval=0.01)

        assert full == "chunk1\nchunk2\n"
        assert mock_client._http.get.call_count == 2

    def test_tail_detached_task_callback(self, mock_client):
        """tail_detached_task fires callback for each chunk"""
        responses = [
            {"task_id": "t1", "output": "A", "is_running": True, "next_offset": 1, "completed": False},
            {"task_id": "t1", "output": "B", "is_running": False, "next_offset": 2, "completed": True},
        ]
        mock_client._http.get.side_effect = responses
        chunks = []
        with patch("time.sleep"):
            mock_client.tail_detached_task("t1", callback=chunks.append)
        assert chunks == ["A", "B"]

    def test_cancel_detached_task(self, mock_client):
        mock_client._http.delete.return_value = None
        assert mock_client.cancel_detached_task("t-abc") is True
        mock_client._http.delete.assert_called_once_with("/detached-tasks/t-abc")

    def test_upload_shortcut(self, mock_client, sample_job_data):
        """upload() runs job and returns first Result"""
        mock_client._http.post_multipart = MagicMock(return_value=sample_job_data)
        with patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=100), \
             patch("os.path.basename", return_value="local.py"), \
             patch("builtins.open", MagicMock()):
            result = mock_client.upload("10.0.0.1", "./local.py", "/tmp/remote.py")
        assert result.ok is True
        call_args = mock_client._http.post_multipart.call_args
        import json as _json
        req = _json.loads(call_args[1]["data"]["request"])
        assert req["file_transfer"]["operation"] == "upload"
        assert req["file_transfer"]["remote_path"] == "/tmp/remote.py"

    def test_download_raises_when_no_download_url(self, mock_client):
        """download() raises NetPulseError when download_url is missing"""
        job_data = {
            "id": "job-dl",
            "status": "finished",
            "result": {
                "type": 1,
                "retval": [{"command": "download", "stdout": "", "ok": True, "metadata": {"host": "10.0.0.1"}}],
            },
            "device_name": "10.0.0.1",
            "command": ["download"],
        }
        mock_client._http.post.return_value = job_data
        with patch("time.sleep"):
            with pytest.raises(NetPulseError, match="no download_url"):
                mock_client.download("10.0.0.1", "/etc/hosts", "/tmp/hosts.txt")

    def test_download_raises_when_result_failed(self, mock_client):
        """download() raises NetPulseError when job result is not ok"""
        job_data = {
            "id": "job-dl",
            "status": "failed",
            "result": {
                "type": 2,
                "retval": [],
                "error": {"type": "connection", "message": "SSH refused"},
            },
            "device_name": "10.0.0.1",
            "command": ["download"],
        }
        mock_client._http.post.return_value = job_data
        with patch("time.sleep"):
            with pytest.raises(NetPulseError, match="Download failed"):
                mock_client.download("10.0.0.1", "/etc/hosts", "/tmp/hosts.txt")
