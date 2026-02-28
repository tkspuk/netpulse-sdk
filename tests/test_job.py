from unittest.mock import patch
from netpulse_sdk import Job

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
