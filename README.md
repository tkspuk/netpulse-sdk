# NetPulse SDK

Python SDK for NetPulse Network Automation Platform.

## Installation

```bash
pip install netpulse-sdk
```

## Quick Start

```python
from netpulse_sdk import NetPulseClient

# Initialize client
client = NetPulseClient(
    base_url="http://localhost:9000",
    api_key="your-api-key",
    default_connection_args={
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "admin",
    },
)

# Query device
result = client.collect("10.1.1.1", "show version").first()
print(result.output)

# Push configuration
job = client.run(devices="10.1.1.1", config=["hostname ROUTER-01"])
print(f"Success: {job.all_ok}")
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
