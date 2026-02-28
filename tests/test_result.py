from netpulse_sdk import Result

class TestResult:
    def test_result_is_success(self):
        # Case 1: Pure success
        res = Result(
            job_id="1", device_id="d1", device_name="n1",
            command="show ip int br", stdout="GigabitEthernet1 up up",
            ok=True
        )
        assert res.is_success is True
        assert res.has_device_error() is False

    def test_result_device_error_detection(self):
        # Case 2: ok is True but stdout has error message
        res = Result(
            job_id="1", device_id="d1", device_name="n1",
            command="conf t", stdout="% Invalid input detected at '^' marker.",
            ok=True
        )
        assert res.is_success is False
        assert res.has_device_error() is True
        assert "Invalid" in res.get_error_lines()[0]

    def test_result_failed_task(self):
        # Case 3: Task itself failed
        res = Result(
            job_id="1", device_id="d1", device_name="n1",
            command="show version", stderr="Connection Refused",
            ok=False
        )
        assert res.is_success is False
        assert res.ok is False
        assert "Connection Refused" in res.stderr

    def test_result_serialization(self):
        res = Result(
            job_id="1", device_id="d1", device_name="n1",
            command="ping", stdout="!!!", ok=True
        )
        d = res.to_dict()
        assert d["job_id"] == "1"
        assert d["stdout"] == "!!!"
        
        json_str = res.to_json()
        assert '"job_id": "1"' in json_str
