import pytest
from unittest.mock import Mock
from netpulse_sdk import NetPulseClient

@pytest.fixture
def mock_client():
    """Provides a client instance with mocking capabilities for Transport"""
    client = NetPulseClient(
        base_url="http://api.test",
        api_key="test-key",
        default_connection_args={
            "device_type": "cisco_ios",
            "username": "admin",
            "password": "password"
        }
    )
    # Mock the internal HTTP client's methods
    client._http.get = Mock()
    client._http.post = Mock()
    client._http.delete = Mock()
    client._http.put = Mock()
    client._http.patch = Mock()
    client._http.session = Mock()
    return client

@pytest.fixture
def sample_job_data():
    """Returns a sample JobInResponse dictionary matching 0.4.0 API"""
    return {
        "id": "job-123",
        "status": "finished",
        "result": {
            "type": 1,  # SUCCESSFUL
            "retval": [
                {
                    "command": "show version",
                    "stdout": "Cisco IOS XE Software, Version 17.03.03",
                    "stderr": "",
                    "exit_status": 0,
                    "metadata": {"host": "10.0.0.1"},
                    "parsed": {"version": "17.03.03"}
                }
            ]
        },
        "device_name": "router-01",
        "command": ["show version"]
    }
