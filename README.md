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

# Collect device information
job = client.collect(
    devices=["10.1.1.1", "10.1.1.2"],
    command="show version",
)

# Process results
for result in job:
    if result.ok:
        print(f"{result.device_name}: {result.output[:50]}...")
    else:
        print(f"{result.device_name}: {result.output}")
```

## Features

- **Batch Execution**: Execute commands on multiple devices simultaneously
- **Configuration Push**: Push configuration changes to network devices
- **Stream Processing**: Process results as they complete
- **Progress Monitoring**: Track job progress in real-time
- **Error Handling**: Comprehensive error handling with detailed error messages
- **Multiple Drivers**: Support for netmiko, napalm, pyeapi, and paramiko

## Supported Drivers

- **netmiko** (default) - Most network devices (Cisco, HP, Huawei, Juniper, etc.)
- **napalm** - Multi-vendor unified interface
- **pyeapi** - Arista devices (eAPI)
- **paramiko** - Linux servers

## License

MIT
