from netpulse_sdk import Result
from netpulse_sdk.result import DetachedTaskLog, DetachedTaskInfo, WorkerInfo, ConnectionTestResult

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

    def test_result_duration_s(self):
        res = Result(job_id="1", device_id="d1", device_name="n1",
                     command="ping", ok=True, duration_ms=1500)
        assert res.duration_s == 1.5

    def test_result_bool_truthiness(self):
        ok = Result(job_id="1", device_id="d1", device_name="n1", command="c", ok=True)
        fail = Result(job_id="1", device_id="d1", device_name="n1", command="c", ok=False)
        assert bool(ok) is True
        assert bool(fail) is False

    def test_detached_task_log_model(self):
        snap = DetachedTaskLog(
            task_id="t1", output="hello\n", is_running=True,
            next_offset=6, completed=False, pid=999,
        )
        assert snap.is_running is True
        assert snap.next_offset == 6
        assert "running" in repr(snap)

    def test_detached_task_log_done_repr(self):
        snap = DetachedTaskLog(task_id="t1", is_running=False, completed=True, next_offset=10)
        assert "done" in repr(snap)

    def test_detached_task_info_repr(self):
        info = DetachedTaskInfo(task_id="t1", host="10.0.0.1", driver="paramiko", status="running")
        assert "t1" in repr(info)
        assert "10.0.0.1" in repr(info)

    def test_worker_info_repr(self):
        w = WorkerInfo(name="worker-1", status="idle")
        assert "worker-1" in repr(w)
        assert "idle" in repr(w)

    def test_connection_test_result_to_dict(self):
        res = ConnectionTestResult(ok=True, host="10.0.0.1", driver="netmiko", duration_ms=50)
        d = res.to_dict()
        assert d["host"] == "10.0.0.1"
        assert d["ok"] is True

    def test_connection_test_result_repr(self):
        res = ConnectionTestResult(ok=False, host="10.0.0.1", driver="netmiko", duration_ms=120)
        r = repr(res)
        assert "FAILED" in r
        assert "120ms" in r
