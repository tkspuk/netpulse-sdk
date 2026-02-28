from unittest.mock import patch
from netpulse_sdk import Job, JobGroup

class TestAdvancedFeatures:
    def test_job_parsed_data(self, mock_client):
        # Result with parsed data
        job_data = {
            "id": "j1",
            "status": "finished",
            "result": {
                "type": 1,
                "retval": [{
                    "command": "show version",
                    "stdout": "...",
                    "parsed": {"version": "1.0", "vendor": "cisco"},
                    "metadata": {"host": "router-01"}
                }]
            }
        }
        job = Job(mock_client, job_data, "router-01", ["show version"])
        
        # Test convenience property (returns direct value for single result mapped by command)
        assert job.parsed["show version"]["version"] == "1.0"
        
    def test_group_parsed_data(self, mock_client):
        job_data_1 = {
            "id": "j1", "status": "finished",
            "result": {"type": 1, "retval": [{"command": "c1", "parsed": {"v": 1}, "metadata": {"host": "d1"}}]}
        }
        job_data_2 = {
            "id": "j2", "status": "finished",
            "result": {"type": 1, "retval": [{"command": "c1", "parsed": {"v": 2}, "metadata": {"host": "d2"}}]}
        }
        job1 = Job(mock_client, job_data_1, "d1", ["c1"])
        job2 = Job(mock_client, job_data_2, "d2", ["c1"])
        group = JobGroup(jobs=[job1, job2])
        
        parsed = group.parsed
        assert parsed["d1"]["c1"]["v"] == 1
        assert parsed["d2"]["c1"]["v"] == 2

    def test_discover_jobs(self, mock_client):
        # Mock list_detached_tasks
        mock_client._http.get.return_value = [
            {
                "task_id": "task_abc",
                "status": "running",
                "command": "tail -f log",
                "driver": "paramiko",
                "metadata": {"host": "10.0.0.5"},
                "created_at": "2024-02-24T12:00:00Z"
            }
        ]
        
        jobs = mock_client.discover_jobs()
        assert len(jobs) == 1
        assert jobs[0].task_id == "task_abc"
        assert jobs[0].device_name == "10.0.0.5"
        assert jobs[0].status == "started" # derived from 'running'
        
    def test_download_file_consistency(self, mock_client):
        from unittest.mock import MagicMock
        
        # mock_client._http.session.stream needs to be a MagicMock to handle __enter__
        mock_stream = MagicMock()
        mock_client._http.session.stream = mock_stream
        
        mock_response = MagicMock()
        mock_response.headers = {"Content-Length": "10"}
        mock_response.iter_bytes.return_value = [b"data"]
        
        # Mock the context manager __enter__ to return the mock_response
        mock_stream.return_value.__enter__.return_value = mock_response
        
        # Mocking os.makedirs and open to avoid side effects
        with patch("os.makedirs"), patch("builtins.open", MagicMock()):
            mock_client.download_file("http://external/file.txt", "/tmp/test.txt")
        
        mock_stream.assert_called_once()
        args, _ = mock_stream.call_args
        assert args[1] == "http://external/file.txt"
