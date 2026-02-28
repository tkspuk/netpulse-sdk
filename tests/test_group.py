from netpulse_sdk.job import Job, JobGroup

class TestJobGroup:
    def test_group_aggregation(self, mock_client, sample_job_data):
        job1 = Job(mock_client, sample_job_data, "d1", ["c1"])
        job2 = Job(mock_client, sample_job_data, "d2", ["c2"])
        
        group = JobGroup(jobs=[job1, job2])
        
        assert len(group) == 2
        assert group.is_done() is True
        
        # Aggregated results
        all_results = group.results()
        assert len(all_results) == 2
        # Result device_name comes from metadata['host'] in sample_job_data
        assert all_results[0].device_name == "10.0.0.1"

    def test_group_stdout_dict(self, mock_client, sample_job_data):
        job1 = Job(mock_client, sample_job_data, "router-01", ["show version"])
        group = JobGroup(jobs=[job1])
        
        # Now stdout is Dict[str, str] for JobGroup (mapped by device_name)
        assert sample_job_data["result"]["retval"][0]["stdout"] in group.stdout["10.0.0.1"]
        
        # Original hierarchical structure is in stdout_dict
        assert group.stdout_dict["10.0.0.1"]["show version"] == sample_job_data["result"]["retval"][0]["stdout"]

    def test_group_truly_succeeded(self, mock_client):
        # One truly success, one with device error
        res_ok = {
            "command": "c1", "stdout": "ok", "ok": True, "exit_status": 0
        }
        res_err = {
            "command": "c2", "stdout": "% Error", "ok": True, "exit_status": 0
        }
        
        job1 = Job(mock_client, {"id": "1", "status": "finished", "result": {"type": 1, "retval": [res_ok]}}, "d1", ["c1"])
        job2 = Job(mock_client, {"id": "2", "status": "finished", "result": {"type": 1, "retval": [res_err]}}, "d2", ["c2"])
        
        group = JobGroup(jobs=[job1, job2])
        
        assert len(group.succeeded()) == 2
        assert len(group.truly_succeeded()) == 1
        assert len(group.device_errors()) == 1
