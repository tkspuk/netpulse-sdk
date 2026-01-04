# NetPulse SDK 全量参数参考

## 目录
- [1. NetPulse 客户端初始化](#1-netpulse-客户端初始化)
- [2. 方法参数](#2-方法参数)
- [3. connection_args 参数](#3-connection_args-参数)
- [4. driver_args 参数](#4-driver_args-参数)
- [5. devices 设备列表格式](#5-devices-设备列表格式)
- [6. credential 凭据配置](#6-credential-凭据配置)
- [7. rendering 模板渲染](#7-rendering-模板渲染)
- [8. parsing 输出解析](#8-parsing-输出解析)
- [9. webhook 回调配置](#9-webhook-回调配置)

---

## 1. NetPulse 客户端初始化

```python
from netpulse_sdk import NetPulseClient

client = NetPulseClient(
    base_url="http://localhost:9000",           # [必需] API 服务地址
    api_key="your-api-key",                     # [必需] API 密钥
    timeout=30,                                 # [可选] HTTP 请求超时时间（秒），默认 30
    driver="netmiko",                           # [可选] 默认驱动，默认 "netmiko"
    default_connection_args={},                 # [可选] 默认连接参数
    pool_connections=10,                        # [可选] 连接池数量，默认 10
    pool_maxsize=200,                           # [可选] 每个连接池最大连接数，默认 200（大规模批量可调整到 500）
    max_retries=3,                              # [可选] HTTP 请求自动重试次数，默认 3
)
```

### 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `base_url` | `str` | ✅ | - | NetPulse API 服务地址，如 `http://localhost:9000` |
| `api_key` | `str` | ✅ | - | API 密钥，从 NetPulse 管理界面获取 |
| `timeout` | `int` | ❌ | `30` | HTTP 请求超时时间（秒） |
| `driver` | `str` | ❌ | `"netmiko"` | 默认驱动：`netmiko`, `napalm`, `pyeapi`, `paramiko` |
| `default_connection_args` | `dict` | ❌ | `{}` | 默认连接参数（用户名、密码等），参见第 3 节 |
| `pool_connections` | `int` | ❌ | `10` | HTTP 连接池数量 |
| `pool_maxsize` | `int` | ❌ | `200` | 每个连接池的最大连接数 |
| `max_retries` | `int` | ❌ | `3` | HTTP 请求失败自动重试次数 |

---

## 2. 方法参数

### 2.1 `run()` 方法（通用执行）

```python
job = client.run(
    devices=["10.1.1.1", "10.1.1.2"],           # [必需] 设备列表
    commands=["show version"],                  # [可选] 查询命令（与 config 互斥）
    config=["hostname ROUTER-01"],              # [可选] 配置命令（与 commands 互斥）
    mode="auto",                                # [可选] 执行模式：auto/exec/bulk
    timeout=300,                                # [可选] 任务超时时间（秒）
    connection_args={},                         # [可选] 连接参数（覆盖默认值）
    driver="netmiko",                           # [可选] 驱动名称（覆盖默认值）
    driver_args={},                             # [可选] 驱动特定参数
    credential={},                              # [可选] Vault 凭据引用
    rendering={},                               # [可选] 模板渲染配置
    parsing={},                                 # [可选] 输出解析配置
    queue_strategy="fifo",                      # [可选] 队列策略：fifo/pinned
    result_ttl=3600,                            # [可选] 结果保留时间（秒）
    webhook={},                                 # [可选] Webhook 回调配置
)
```

### 2.2 `collect()` 方法（只读查询）

```python
job = client.collect(
    devices=["10.1.1.1"],                       # [必需] 设备列表
    commands=["show version"],                  # [必需] 查询命令
    timeout=300,                                # [可选] 任务超时时间（秒）
    connection_args={},                         # [可选] 连接参数
    driver="netmiko",                           # [可选] 驱动名称
    driver_args={},                             # [可选] 驱动特定参数
    credential={},                              # [可选] Vault 凭据引用
    parsing={},                                 # [可选] 输出解析配置
    queue_strategy="fifo",                      # [可选] 队列策略
    result_ttl=3600,                            # [可选] 结果保留时间（秒）
    webhook={},                                 # [可选] Webhook 回调配置
)
```

### 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `devices` | `str` / `list` | ✅ | - | 设备列表，详见第 5 节 |
| `commands` | `str` / `list` | ✅* | - | 查询命令（与 config 互斥） |
| `config` | `str` / `list` | ✅* | - | 配置命令（与 commands 互斥） |
| `mode` | `str` | ❌ | `"auto"` | 执行模式：`auto`（自动选择）、`exec`（单设备）、`bulk`（批量） |
| `timeout` | `int` | ❌ | `300` | 任务超时时间（秒），对应 API 的 `ttl` 参数 |
| `connection_args` | `dict` | ❌ | `{}` | 连接参数，覆盖 `default_connection_args` |
| `driver` | `str` | ❌ | 客户端默认 | 驱动名称，覆盖客户端默认驱动 |
| `driver_args` | `dict` | ❌ | `None` | 驱动特定参数，详见第 4 节 |
| `credential` | `dict` | ❌ | `None` | Vault 凭据引用，详见第 6 节 |
| `rendering` | `dict` | ❌ | `None` | 模板渲染配置，详见第 7 节 |
| `parsing` | `dict` | ❌ | `None` | 输出解析配置，详见第 8 节 |
| `queue_strategy` | `str` | ❌ | `None` | 队列策略：`fifo`（先进先出）、`pinned`（固定 Worker） |
| `result_ttl` | `int` | ❌ | `None` | 结果保留时间（秒） |
| `webhook` | `dict` | ❌ | `None` | Webhook 回调配置，详见第 9 节 |

---

## 3. connection_args 参数

### 3.1 Netmiko 驱动（默认）

适用于大多数网络设备（Cisco、HP、Huawei、Juniper 等）

```python
connection_args = {
    "device_type": "cisco_ios",     # [必需] 设备类型，参见 netmiko 支持列表
    "host": "10.1.1.1",             # [自动] 由 devices 参数提供，通常不需要手动指定
    "username": "admin",            # [必需] 用户名
    "password": "password",         # [必需] 密码
    "port": 22,                     # [可选] SSH 端口，默认 22
    "secret": "",                   # [可选] Enable 密码（Cisco）
    "timeout": 60,                  # [可选] 连接超时（秒）
    "session_timeout": 60,          # [可选] 会话超时（秒）
    "auth_timeout": None,           # [可选] 认证超时（秒）
    "banner_timeout": 15,           # [可选] Banner 超时（秒）
    "global_delay_factor": 1,       # [可选] 全局延迟因子
    "allow_auto_change": False,     # [可选] 允许自动更改设备类型
}
```

**常见 device_type：**
- Cisco IOS/IOS-XE: `cisco_ios`
- Cisco IOS-XR: `cisco_xr`
- Cisco NX-OS: `cisco_nxos`
- HP Comware: `hp_comware`
- Huawei: `huawei`, `huawei_vrpv8`
- Juniper Junos: `juniper_junos`
- Arista EOS: `arista_eos`

完整列表：https://github.com/ktbyers/netmiko/blob/develop/PLATFORMS.md

### 3.2 PyEAPI 驱动（Arista 专用）

```python
connection_args = {
    "host": "10.1.1.1",             # [必需] 设备 IP
    "username": "admin",            # [必需] 用户名
    "password": "admin",            # [必需] 密码
    "transport": "https",           # [可选] 传输协议：https/http，默认 https
    "port": 443,                    # [可选] 端口，https=443, http=80
    "timeout": 60,                  # [可选] 连接超时（秒）
}
```

### 3.3 Paramiko 驱动（Linux 服务器）

```python
connection_args = {
    "host": "10.1.1.1",             # [必需] 服务器 IP
    "username": "root",             # [必需] 用户名
    "password": "password",         # [可选] 密码（与 key_filename 二选一）
    "key_filename": "/path/to/key", # [可选] SSH 私钥路径（与 password 二选一）
    "port": 22,                     # [可选] SSH 端口，默认 22
    "timeout": 60,                  # [可选] 连接超时（秒）
    "look_for_keys": True,          # [可选] 自动查找 SSH 密钥
    "allow_agent": True,            # [可选] 允许使用 SSH Agent
}
```

### 3.4 NAPALM 驱动（跨厂商）

```python
connection_args = {
    "device_type": "ios",           # [必需] 设备类型：ios, iosxr, nxos, junos, eos
    "hostname": "10.1.1.1",         # [必需] 设备 IP（注意是 hostname 不是 host）
    "username": "admin",            # [必需] 用户名
    "password": "password",         # [必需] 密码
    "timeout": 60,                  # [可选] 连接超时（秒）
    "optional_args": {},            # [可选] 厂商特定参数
}
```

---

## 4. driver_args 参数

驱动特定参数，用于优化性能和行为。

### 4.1 Netmiko driver_args

```python
driver_args = {
    # === 性能优化 ===
    "read_timeout": 60,             # [可选] 读取超时（秒），默认 10
    "delay_factor": 2,              # [可选] 延迟因子（慢速设备增大），默认 1
    "max_loops": 1000,              # [可选] 最大循环次数，默认 500
    "global_delay_factor": 1,       # [可选] 全局延迟因子，默认 1
    
    # === 输出处理 ===
    "strip_prompt": True,           # [可选] 去除提示符，默认 True
    "strip_command": True,          # [可选] 去除命令回显，默认 True
    "normalize": True,              # [可选] 标准化输出（去除\r），默认 True
    "use_textfsm": False,           # [可选] 使用 TextFSM 解析，默认 False
    
    # === 连接行为 ===
    "fast_cli": True,               # [可选] 快速 CLI 模式，默认 True
    "session_log": None,            # [可选] 会话日志文件路径
    "conn_timeout": 10,             # [可选] 连接超时（秒），默认 10
    "auth_timeout": None,           # [可选] 认证超时（秒）
    "banner_timeout": 15,           # [可选] Banner 超时（秒）
    
    # === 分页处理 ===
    "auto_find_prompt": True,       # [可选] 自动查找提示符，默认 True
    "expect_string": None,          # [可选] 自定义期望字符串
}
```

### 4.2 PyEAPI driver_args

```python
driver_args = {
    "encoding": "json",             # [可选] 输出格式：json/text，默认 json
    "autoComplete": False,          # [可选] 自动补全命令，默认 False
    "expandAliases": False,         # [可选] 展开别名，默认 False
}
```

### 4.3 Paramiko driver_args

```python
driver_args = {
    "timeout": 30,                  # [可选] 命令执行超时（秒）
    "encoding": "utf-8",            # [可选] 字符编码，默认 utf-8
}
```

### 4.4 NAPALM driver_args

```python
driver_args = {
    "optional_args": {},            # [可选] 传递给底层驱动的参数
}
```

---

## 5. devices 设备列表格式

### 5.1 基本格式

```python
# 格式1：单个设备（字符串）
devices = "10.1.1.1"

# 格式2：多个设备（字符串列表）
devices = ["10.1.1.1", "10.1.1.2", "10.1.1.3"]

# 格式3：单个设备（字典）
devices = {
    "host": "10.1.1.1",
    "username": "admin",
    "password": "password",
}

# 格式4：多个设备（字典列表）
devices = [
    {"host": "10.1.1.1"},
    {"host": "10.1.1.2"},
]
```

### 5.2 每设备不同参数

```python
# 每个设备可以覆盖连接参数
devices = [
    {
        "host": "10.1.1.1",
        "username": "admin",        # 覆盖用户名
        "password": "pass1",        # 覆盖密码
    },
    {
        "host": "10.1.1.2",
        "device_type": "cisco_ios", # 覆盖设备类型
        "port": 2222,               # 覆盖端口
    },
]
```

### 5.3 每设备不同命令（新特性）🆕

```python
# 混合使用：部分设备使用 base 命令，部分覆盖
devices = [
    "10.1.1.1",                                         # 使用 base 命令
    {"host": "10.1.1.2", "command": "show power"},     # 覆盖命令
    {"host": "10.1.1.3", "command": "show inventory"}, # 覆盖命令
]

job = client.collect(
    devices=devices,
    commands="show version",  # base 命令
)
```

```python
# 每设备不同配置
devices = [
    {"host": "10.1.1.1", "config": "hostname ROUTER-01"},
    {"host": "10.1.1.2", "config": "hostname ROUTER-02"},
]

job = client.run(
    devices=devices,
    config="hostname DEFAULT",  # base 配置
)
```

```python
# 每设备多条命令
devices = [
    {
        "host": "10.1.1.1",
        "command": ["show version", "show run"]  # 命令列表
    },
    {
        "host": "10.1.1.2",
        "command": "show power"  # 单个命令
    },
]
```

---

## 6. credential 凭据配置

从 Vault 获取凭据（需要配置 Vault 集成）

```python
credential = {
    "name": "network-devices",      # [可选] 凭据名称
    "ref": "secret/data/network",   # [可选] Vault 路径
    "mount": "kv",                  # [可选] Vault 挂载点
    "field_mapping": {              # [可选] 字段映射
        "username": "user",
        "password": "pass",
    },
}
```

示例：
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

## 7. rendering 模板渲染

使用 Jinja2 模板渲染命令

```python
rendering = {
    "name": "template-name",        # [可选] 模板名称（从数据库加载）
    "template": "show vlan {{ id }}", # [可选] 内联模板
    "context": {                    # [必需] 模板变量
        "id": 100,
        "name": "DATA",
    },
}
```

示例：
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

## 8. parsing 输出解析

使用解析模板处理输出

```python
parsing = {
    "name": "parser-name",          # [可选] 解析器名称（从数据库加载）
    "template": "textfsm_template", # [可选] 内联模板
    "engine": "textfsm",            # [可选] 解析引擎：textfsm/ttp/genie
    "context": {},                  # [可选] 解析器上下文
}
```

示例：
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

## 9. webhook 回调配置

任务完成后触发 HTTP 回调

```python
webhook = {
    "url": "https://api.example.com/callback",  # [必需] 回调 URL
    "method": "POST",                           # [可选] HTTP 方法，默认 POST
    "headers": {                                # [可选] 自定义 Headers
        "Authorization": "Bearer token",
        "Content-Type": "application/json",
    },
    "body": {                                   # [可选] 自定义 Body
        "job_id": "{{ job_id }}",
        "status": "{{ status }}",
    },
    "timeout": 30,                              # [可选] 回调超时（秒）
    "retry": 3,                                 # [可选] 重试次数
}
```

示例：
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

## 常见组合示例

### 示例1：基础查询

```python
job = client.collect(
    devices=["10.1.1.1", "10.1.1.2"],
    commands="show version",
)
```

### 示例2：慢速设备优化

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

### 示例3：批量配置推送

```python
job = client.run(
    devices=["10.1.1.1", "10.1.1.2"],
    config=["vlan 100", "name DATA"],
    queue_strategy="pinned",
)
```

### 示例4：每设备不同命令

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

### 示例5：使用 Vault 凭据

```python
job = client.collect(
    devices="10.1.1.1",
    commands="show version",
    credential={
        "ref": "secret/data/network/cisco",
    },
)
```

### 示例6：Webhook 通知

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

## 快速参考表

### 队列策略对比

| 策略 | 适用场景 | 优势 | 劣势 |
|------|----------|------|------|
| `fifo` | 临时、一次性操作 | 公平调度 | 每次新建连接 |
| `pinned` | 频繁操作同一设备 | 复用连接，快速 | 占用 Worker |

### 超时时间设置建议

| 操作类型 | timeout | driver_args.read_timeout |
|---------|---------|--------------------------|
| 简单查询 | 300 | 30 |
| 大量输出 | 600 | 60-120 |
| 配置推送 | 300-600 | 30-60 |
| 慢速设备 | 600-1800 | 120+ |

### 驱动选择指南

| 设备类型 | 推荐驱动 | 备用驱动 |
|---------|---------|---------|
| Cisco IOS | netmiko | napalm |
| Cisco NX-OS | netmiko | napalm |
| Arista EOS | pyeapi | netmiko |
| Juniper Junos | netmiko | napalm |
| HP/Huawei | netmiko | - |
| Linux 服务器 | paramiko | - |

---

## 相关文档

- **完整示例**：`examples/README.md`
- **驱动指南**：`examples/DRIVER_GUIDE.md`
- **Bulk 增强特性**：`docs/BULK_PER_DEVICE_COMMANDS.md`
- **SDK 文档**：`README.md`

