## Version Compatibility

| SDK Version | NetPulse API Version | Status |
|-------------|----------------------|--------|
| **0.3.x**   | **0.4.0+**           | Recommended |
| 0.2.x       | 0.3.x                | Legacy |

> **IMPORTANT**: This version of the SDK (0.3.x) is strictly aligned with NetPulse API 0.4.0. It uses `stdout`, `stderr`, and `ok` as standard fields.

## Installation

```bash
pip install netpulse-sdk
```
local-install
```bash
pip install -e .
```

# NetPulse SDK

Python SDK for NetPulse Network Automation Platform.

## Quick Start

```python
from netpulse_sdk import NetPulseClient

# Initialize client
client = NetPulseClient(
    base_url="http://localhost:9000",
    api_key="your-api-key",
)

# Query device (Recommended pattern)
job = client.collect(
    devices="10.1.1.1", 
    command="show version",
    driver="netmiko",
    connection_args={"device_type": "cisco_ios", "username": "admin", "password": "..."}
)

if job: # Uses new __bool__ feature to check all_ok
    result = job[0] # Prefer index over .first()
    print(f"Output: {result.stdout}")

# Push configuration
job = client.run(devices="10.1.1.1", config=["hostname ROUTER-01"]).raise_on_error()
print("Configuration success")
```

## Features

- **Batch Execution**: Execute commands on multiple devices simultaneously
- **Configuration Push**: Push configuration changes to network devices
- **Multiple Drivers**: Support for netmiko, napalm, pyeapi, and paramiko
- **Progress Monitoring**: Track job progress in real-time
- **Error Handling**: Comprehensive error handling with detailed error messages

## Supported Drivers

| Driver | Use Case |
|--------|----------|
| `netmiko` | Network devices (Cisco, HP, Huawei, Juniper) |
| `paramiko` | Linux servers |
| `pyeapi` | Arista (eAPI) |
| `napalm` | Multi-vendor unified interface |

## Documentation

- [Examples](examples/README.md)
- [Parameter Reference](docs/PARAMETERS_REFERENCE.md)

## License

MIT
