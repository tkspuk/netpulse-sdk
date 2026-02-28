from unittest.mock import patch
from netpulse_sdk import NetPulseClient, Job
from netpulse_sdk.result import ConnectionTestResult

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
