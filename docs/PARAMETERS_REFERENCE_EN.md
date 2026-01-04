# NetPulse SDK Parameters Reference

## Table of Contents
- [1. NetPulse Client Initialization](#1-netpulse-client-initialization)
- [2. Method Parameters](#2-method-parameters)
- [3. connection_args Parameters](#3-connection_args-parameters)
- [4. driver_args Parameters](#4-driver_args-parameters)
- [5. devices List Format](#5-devices-list-format)
- [6. credential Configuration](#6-credential-configuration)
- [7. rendering Template Rendering](#7-rendering-template-rendering)
- [8. parsing Output Parsing](#8-parsing-output-parsing)
- [9. webhook Callback Configuration](#9-webhook-callback-configuration)

---

## 1. NetPulse Client Initialization

```python
from netpulse_sdk import NetPulseClient

client = NetPulseClient(
    base_url="http://localhost:9000",           # [Required] API service URL
    api_key="your-api-key",                     # [Required] API key
    timeout=30,                                 # [Optional] HTTP request timeout (seconds), default 30
    driver="netmiko",                           # [Optional] Default driver, default "netmiko"
    default_connection_args={},                 # [Optional] Default connection parameters
    pool_connections=10,                        # [Optional] Connection pool count, default 10
    pool_maxsize=200,                           # [Optional] Max connections per pool, default 200 (increase to 500 for large batches)
    max_retries=3,                              # [Optional] HTTP request auto-retry count, default 3
)
```

### Parameter Description

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `base_url` | `str` | ✅ | - | NetPulse API service URL, e.g., `http://localhost:9000` |
| `api_key` | `str` | ✅ | - | API key obtained from NetPulse management interface |
| `timeout` | `int` | ❌ | `30` | HTTP request timeout (seconds) |
| `driver` | `str` | ❌ | `"netmiko"` | Default driver: `netmiko`, `napalm`, `pyeapi`, `paramiko` |
| `default_connection_args` | `dict` | ❌ | `{}` | Default connection parameters (username, password, etc.), see Section 3 |
| `pool_connections` | `int` | ❌ | `10` | HTTP connection pool count |
| `pool_maxsize` | `int` | ❌ | `200` | Maximum connections per pool |
| `max_retries` | `int` | ❌ | `3` | HTTP request auto-retry count on failure |

---

## 2. Method Parameters

### 2.1 `run()` Method (General Execution)

```python
job = client.run(
    devices=["10.1.1.1", "10.1.1.2"],           # [Required] Device list
    commands=["show version"],                  # [Optional] Query commands (mutually exclusive with config)
    config=["hostname ROUTER-01"],              # [Optional] Configuration commands (mutually exclusive with commands)
    mode="auto",                                # [Optional] Execution mode: auto/exec/bulk
    timeout=300,                                # [Optional] Task timeout (seconds)
    connection_args={},                         # [Optional] Connection parameters (override defaults)
    driver="netmiko",                           # [Optional] Driver name (override default)
    driver_args={},                             # [Optional] Driver-specific parameters
    credential={},                              # [Optional] Vault credential reference
    rendering={},                               # [Optional] Template rendering configuration
    parsing={},                                 # [Optional] Output parsing configuration
    queue_strategy="fifo",                      # [Optional] Queue strategy: fifo/pinned
    result_ttl=3600,                            # [Optional] Result retention time (seconds)
    webhook={},                                 # [Optional] Webhook callback configuration
)
```

### 2.2 `collect()` Method (Read-Only Query)

```python
job = client.collect(
    devices=["10.1.1.1"],                       # [Required] Device list
    commands=["show version"],                  # [Required] Query commands
    timeout=300,                                # [Optional] Task timeout (seconds)
    connection_args={},                         # [Optional] Connection parameters
    driver="netmiko",                           # [Optional] Driver name
    driver_args={},                             # [Optional] Driver-specific parameters
    credential={},                              # [Optional] Vault credential reference
    parsing={},                                 # [Optional] Output parsing configuration
    queue_strategy="fifo",                      # [Optional] Queue strategy
    result_ttl=3600,                            # [Optional] Result retention time (seconds)
    webhook={},                                 # [Optional] Webhook callback configuration
)
```

### Parameter Description

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `devices` | `str` / `list` | ✅ | - | Device list, see Section 5 |
| `commands` | `str` / `list` | ✅* | - | Query commands (mutually exclusive with config) |
| `config` | `str` / `list` | ✅* | - | Configuration commands (mutually exclusive with commands) |
| `mode` | `str` | ❌ | `"auto"` | Execution mode: `auto` (auto-select), `exec` (single device), `bulk` (batch) |
| `timeout` | `int` | ❌ | `300` | Task timeout (seconds), corresponds to API's `ttl` parameter |
| `connection_args` | `dict` | ❌ | `{}` | Connection parameters, override `default_connection_args` |
| `driver` | `str` | ❌ | Client default | Driver name, override client default driver |
| `driver_args` | `dict` | ❌ | `None` | Driver-specific parameters, see Section 4 |
| `credential` | `dict` | ❌ | `None` | Vault credential reference, see Section 6 |
| `rendering` | `dict` | ❌ | `None` | Template rendering configuration, see Section 7 |
| `parsing` | `dict` | ❌ | `None` | Output parsing configuration, see Section 8 |
| `queue_strategy` | `str` | ❌ | `None` | Queue strategy: `fifo` (first-in-first-out), `pinned` (fixed worker) |
| `result_ttl` | `int` | ❌ | `None` | Result retention time (seconds) |
| `webhook` | `dict` | ❌ | `None` | Webhook callback configuration, see Section 9 |

---

## 3. connection_args Parameters

### 3.1 Netmiko Driver (Default)

Suitable for most network devices (Cisco, HP, Huawei, Juniper, etc.)

```python
connection_args = {
    "device_type": "cisco_ios",     # [Required] Device type, see netmiko support list
    "host": "10.1.1.1",             # [Auto] Provided by devices parameter, usually no need to specify manually
    "username": "admin",            # [Required] Username
    "password": "password",         # [Required] Password
    "port": 22,                     # [Optional] SSH port, default 22
    "secret": "",                   # [Optional] Enable password (Cisco)
    "timeout": 60,                  # [Optional] Connection timeout (seconds)
    "session_timeout": 60,          # [Optional] Session timeout (seconds)
    "auth_timeout": None,           # [Optional] Authentication timeout (seconds)
    "banner_timeout": 15,           # [Optional] Banner timeout (seconds)
    "global_delay_factor": 1,       # [Optional] Global delay factor
    "allow_auto_change": False,     # [Optional] Allow automatic device type change
}
```

**Common device_type:**
- Cisco IOS/IOS-XE: `cisco_ios`
- Cisco IOS-XR: `cisco_xr`
- Cisco NX-OS: `cisco_nxos`
- HP Comware: `hp_comware`
- Huawei: `huawei`, `huawei_vrpv8`
- Juniper Junos: `juniper_junos`
- Arista EOS: `arista_eos`

Full list: https://github.com/ktbyers/netmiko/blob/develop/PLATFORMS.md

### 3.2 PyEAPI Driver (Arista Specific)

```python
connection_args = {
    "host": "10.1.1.1",             # [Required] Device IP
    "username": "admin",            # [Required] Username
    "password": "admin",            # [Required] Password
    "transport": "https",           # [Optional] Transport protocol: https/http, default https
    "port": 443,                    # [Optional] Port, https=443, http=80
    "timeout": 60,                  # [Optional] Connection timeout (seconds)
}
```

### 3.3 Paramiko Driver (Linux Servers)

```python
connection_args = {
    "host": "10.1.1.1",             # [Required] Server IP
    "username": "root",             # [Required] Username
    "password": "password",         # [Optional] Password (choose one with key_filename)
    "key_filename": "/path/to/key", # [Optional] SSH private key path (choose one with password)
    "port": 22,                     # [Optional] SSH port, default 22
    "timeout": 60,                  # [Optional] Connection timeout (seconds)
    "look_for_keys": True,          # [Optional] Automatically search for SSH keys
    "allow_agent": True,            # [Optional] Allow using SSH Agent
}
```

### 3.4 NAPALM Driver (Multi-Vendor)

```python
connection_args = {
    "device_type": "ios",           # [Required] Device type: ios, iosxr, nxos, junos, eos
    "hostname": "10.1.1.1",         # [Required] Device IP (note: hostname not host)
    "username": "admin",            # [Required] Username
    "password": "password",         # [Required] Password
    "timeout": 60,                  # [Optional] Connection timeout (seconds)
    "optional_args": {},            # [Optional] Vendor-specific parameters
}
```

---

## 4. driver_args Parameters

Driver-specific parameters for performance optimization and behavior control.

### 4.1 Netmiko driver_args

```python
driver_args = {
    # === Performance Optimization ===
    "read_timeout": 60,             # [Optional] Read timeout (seconds), default 10
    "delay_factor": 2,              # [Optional] Delay factor (increase for slow devices), default 1
    "max_loops": 1000,              # [Optional] Maximum loop count, default 500
    "global_delay_factor": 1,       # [Optional] Global delay factor, default 1
    
    # === Output Processing ===
    "strip_prompt": True,           # [Optional] Strip prompt, default True
    "strip_command": True,          # [Optional] Strip command echo, default True
    "normalize": True,              # [Optional] Normalize output (remove \r), default True
    "use_textfsm": False,           # [Optional] Use TextFSM parsing, default False
    
    # === Connection Behavior ===
    "fast_cli": True,               # [Optional] Fast CLI mode, default True
    "session_log": None,            # [Optional] Session log file path
    "conn_timeout": 10,             # [Optional] Connection timeout (seconds), default 10
    "auth_timeout": None,           # [Optional] Authentication timeout (seconds)
    "banner_timeout": 15,           # [Optional] Banner timeout (seconds)
    
    # === Pagination Handling ===
    "auto_find_prompt": True,       # [Optional] Auto find prompt, default True
    "expect_string": None,          # [Optional] Custom expect string
}
```

### 4.2 PyEAPI driver_args

```python
driver_args = {
    "encoding": "json",             # [Optional] Output format: json/text, default json
    "autoComplete": False,          # [Optional] Auto-complete commands, default False
    "expandAliases": False,         # [Optional] Expand aliases, default False
}
```

### 4.3 Paramiko driver_args

```python
driver_args = {
    "timeout": 30,                  # [Optional] Command execution timeout (seconds)
    "encoding": "utf-8",            # [Optional] Character encoding, default utf-8
}
```

### 4.4 NAPALM driver_args

```python
driver_args = {
    "optional_args": {},            # [Optional] Parameters passed to underlying driver
}
```

---

## 5. devices List Format

### 5.1 Basic Format

```python
# Format 1: Single device (string)
devices = "10.1.1.1"

# Format 2: Multiple devices (string list)
devices = ["10.1.1.1", "10.1.1.2", "10.1.1.3"]

# Format 3: Single device (dictionary)
devices = {
    "host": "10.1.1.1",
    "username": "admin",
    "password": "password",
}

# Format 4: Multiple devices (dictionary list)
devices = [
    {"host": "10.1.1.1"},
    {"host": "10.1.1.2"},
]
```

### 5.2 Per-Device Different Parameters

```python
# Each device can override connection parameters
devices = [
    {
        "host": "10.1.1.1",
        "username": "admin",        # Override username
        "password": "pass1",        # Override password
    },
    {
        "host": "10.1.1.2",
        "device_type": "cisco_ios", # Override device type
        "port": 2222,               # Override port
    },
]
```

### 5.3 Per-Device Different Commands (New Feature) 🆕

```python
# Mixed usage: some devices use base command, some override
devices = [
    "10.1.1.1",                                         # Use base command
    {"host": "10.1.1.2", "command": "show power"},     # Override command
    {"host": "10.1.1.3", "command": "show inventory"}, # Override command
]

job = client.collect(
    devices=devices,
    commands="show version",  # base command
)
```

```python
# Per-device different configuration
devices = [
    {"host": "10.1.1.1", "config": "hostname ROUTER-01"},
    {"host": "10.1.1.2", "config": "hostname ROUTER-02"},
]

job = client.run(
    devices=devices,
    config="hostname DEFAULT",  # base configuration
)
```

```python
# Per-device multiple commands
devices = [
    {
        "host": "10.1.1.1",
        "command": ["show version", "show run"]  # Command list
    },
    {
        "host": "10.1.1.2",
        "command": "show power"  # Single command
    },
]
```

---

## 6. credential Configuration

Retrieve credentials from Vault (requires Vault integration configuration)

```python
credential = {
    "name": "network-devices",      # [Optional] Credential name
    "ref": "secret/data/network",   # [Optional] Vault path
    "mount": "kv",                  # [Optional] Vault mount point
    "field_mapping": {              # [Optional] Field mapping
        "username": "user",
        "password": "pass",
    },
}
```

Example:
```python
job = client.collect(
    devices="10.1.1.1",
    commands="show version",
    credential={
        "ref": "secret/data/network/cisco",
        "field_mapping": {
            "username": "cisco_user",
            "password": "cisco_pass",
        },
    },
)
```

---

## 7. rendering Template Rendering

Use Jinja2 templates to render commands

```python
rendering = {
    "name": "template-name",        # [Optional] Template name (load from database)
    "template": "show vlan {{ id }}", # [Optional] Inline template
    "context": {                    # [Required] Template variables
        "id": 100,
        "name": "DATA",
    },
}
```

Example:
```python
job = client.collect(
    devices="10.1.1.1",
    commands="show vlan {{ vlan_id }}",
    rendering={
        "template": "show vlan {{ vlan_id }}",
        "context": {"vlan_id": 100},
    },
)
```

---

## 8. parsing Output Parsing

Use parsing templates to process output

```python
parsing = {
    "name": "parser-name",          # [Optional] Parser name (load from database)
    "template": "textfsm_template", # [Optional] Inline template
    "engine": "textfsm",            # [Optional] Parsing engine: textfsm/ttp/genie
    "context": {},                  # [Optional] Parser context
}
```

Example:
```python
job = client.collect(
    devices="10.1.1.1",
    commands="show version",
    parsing={
        "engine": "textfsm",
        "template": "cisco_ios_show_version.textfsm",
    },
)
```

---

## 9. webhook Callback Configuration

Trigger HTTP callback after task completion

```python
webhook = {
    "url": "https://api.example.com/callback",  # [Required] Callback URL
    "method": "POST",                           # [Optional] HTTP method, default POST
    "headers": {                                # [Optional] Custom headers
        "Authorization": "Bearer token",
        "Content-Type": "application/json",
    },
    "body": {                                   # [Optional] Custom body
        "job_id": "{{ job_id }}",
        "status": "{{ status }}",
    },
    "timeout": 30,                              # [Optional] Callback timeout (seconds)
    "retry": 3,                                 # [Optional] Retry count
}
```

Example:
```python
job = client.collect(
    devices="10.1.1.1",
    commands="show version",
    webhook={
        "url": "https://api.example.com/notifications",
        "method": "POST",
        "headers": {
            "X-API-Key": "your-api-key",
        },
    },
)
```

---

## Common Usage Examples

### Example 1: Basic Query

```python
job = client.collect(
    devices=["10.1.1.1", "10.1.1.2"],
    commands="show version",
)
```

### Example 2: Slow Device Optimization

```python
job = client.collect(
    devices="10.1.1.1",
    commands="show running-config",
    timeout=600,
    driver_args={
        "read_timeout": 120,
        "delay_factor": 2,
        "max_loops": 1000,
    },
)
```

### Example 3: Batch Configuration Push

```python
job = client.run(
    devices=["10.1.1.1", "10.1.1.2"],
    config=["vlan 100", "name DATA"],
    queue_strategy="pinned",
)
```

### Example 4: Per-Device Different Commands

```python
job = client.collect(
    devices=[
        "10.1.1.1",
        {"host": "10.1.1.2", "command": "show power"},
        {"host": "10.1.1.3", "command": "show environment"},
    ],
    commands="show version",
)
```

### Example 5: Using Vault Credentials

```python
job = client.collect(
    devices="10.1.1.1",
    commands="show version",
    credential={
        "ref": "secret/data/network/cisco",
    },
)
```

### Example 6: Webhook Notification

```python
job = client.collect(
    devices=["10.1.1.1", "10.1.1.2"],
    commands="show version",
    webhook={
        "url": "https://api.example.com/notify",
    },
)
```

---

## Quick Reference Tables

### Queue Strategy Comparison

| Strategy | Use Case | Advantages | Disadvantages |
|----------|----------|------------|---------------|
| `fifo` | Temporary, one-time operations | Fair scheduling | New connection each time |
| `pinned` | Frequent operations on same device | Connection reuse, fast | Occupies worker |

### Timeout Settings Recommendations

| Operation Type | timeout | driver_args.read_timeout |
|----------------|---------|--------------------------|
| Simple query | 300 | 30 |
| Large output | 600 | 60-120 |
| Configuration push | 300-600 | 30-60 |
| Slow device | 600-1800 | 120+ |

### Driver Selection Guide

| Device Type | Recommended Driver | Alternative Driver |
|-------------|-------------------|-------------------|
| Cisco IOS | netmiko | napalm |
| Cisco NX-OS | netmiko | napalm |
| Arista EOS | pyeapi | netmiko |
| Juniper Junos | netmiko | napalm |
| HP/Huawei | netmiko | - |
| Linux Servers | paramiko | - |

---

## Related Documentation

- **Complete Examples**: `examples/README.md`
- **Driver Guide**: `examples/DRIVER_GUIDE.md`
- **Bulk Enhancement Feature**: `docs/BULK_PER_DEVICE_COMMANDS.md`
- **SDK Documentation**: `README.md`

