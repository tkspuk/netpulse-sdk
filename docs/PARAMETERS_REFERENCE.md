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
- [10. Result 对象](#10-result-对象)
- [11. Job 对象](#11-job-对象)

---

## 1. NetPulse 客户端初始化

```python
from netpulse_sdk import NetPulseClient

# 方式1: 显式传参
client = NetPulseClient(
    base_url="http://localhost:9000",           # [必需*] API 服务地址
    api_key="your-api-key",                     # [必需*] API 密钥
    timeout=30,                                 # [可选] HTTP 请求超时（秒），默认 30
    driver="netmiko",                           # [可选] 默认驱动，默认 "netmiko"
    default_connection_args={},                 # [可选] 默认连接参数
    default_credential=None,                    # [可选] 默认 Vault 凭据引用
    pool_connections=10,                        # [可选] 连接池数量，默认 10
    pool_maxsize=200,                           # [可选] 最大连接数，默认 200
    max_retries=3,                              # [可选] 自动重试次数，默认 3
    profile="default",                          # [可选] 配置配置文件名称，默认 "default"
    config_path=None,                           # [可选] 显式指定配置文件路径
    enable_mode=False,                          # [可选] 默认 enable 模式 (Netmiko)
    save=False,                                 # [可选] 默认保存配置模式 (Netmiko)
    api_key_name="X-API-KEY",                   # [可选] API Key Header 名称
)

# 方式2: 环境变量（自动读取 NETPULSE_URL, NETPULSE_API_KEY）
client = NetPulseClient(driver="netmiko", default_connection_args={...})

# 方式3: Context Manager（自动关闭连接）
with NetPulseClient() as client:
    client.ping()  # 健康检查
    ...
```

### 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `base_url` | `str` | ✅* | 环境变量 | API 地址，可从 `NETPULSE_URL` 读取 |
| `api_key` | `str` | ✅* | 环境变量 | API 密钥，可从 `NETPULSE_API_KEY` 读取 |
| `timeout` | `int` | ❌ | `30` | HTTP 请求超时（秒） |
| `driver` | `str` | ❌ | `"netmiko"` | 驱动：`netmiko`, `napalm`, `pyeapi`, `paramiko` |
| `default_connection_args` | `dict` | ❌ | `{}` | 默认连接参数，详见第 3 节 |
| `default_credential` | `dict` | ❌ | `None` | 默认 Vault 凭据引用，详见第 6 节 |
| `pool_connections` | `int` | ❌ | `10` | HTTP 连接池数量 |
| `pool_maxsize` | `int` | ❌ | `200` | 每池最大连接数（大批量可调至 500） |
| `max_retries` | `int` | ❌ | `3` | HTTP 请求失败自动重试次数 |
| `profile` | `str` | ❌ | `"default"` | 配置文件 Profile 名称 |
| `config_path` | `str` | ❌ | `None` | 显式指定 `.netmiko.yaml` 或 `.netpulse.yaml` 路径 |
| `enable_mode` | `bool` | ❌ | `False` | 默认是否进入全局特权模式 |
| `save` | `bool` | ❌ | `False` | 默认是否在执行后保存配置 |
| `api_key_name` | `str` | ❌ | `"X-API-KEY"` | API Key 的 Header 名称 |

### 客户端方法

| 方法 | 说明 |
|------|------|
| `ping()` | 健康检查，返回 `True` 或抛出异常 |
| `close()` | 关闭 HTTP 连接池 |
| `test_connection(...)` | 测试单个设备连接 |
| `test_connections(...)` | 批量测试多设备连接 |
| `run(...)` | 执行命令/配置，详见 2.1 |
| `collect(...)` | 通用查询（只读），详见 2.2 |
| `get_job(id)` | 获取指定任务详情 |
| `list_jobs(...)` | 列出历史任务 (`List[Job]`) |
| `cancel_job(id)` | 取消或删除任务 |
| `list_workers(...)` | 查看后端 Worker 状态 (`List[WorkerInfo]`) |
| `delete_worker(name)`| 删除单个后台 Worker |
| `delete_workers(...)`| 批量删除后端 Worker (按条件) |
| `render_template(...)` | 独立调用模板渲染功能 |
| `parse_template(...)` | 独立调用输出解析功能 |

---

## 2. 方法参数

### 2.1 `run()` 方法（通用执行）

```python
job = client.run(
    devices=["10.1.1.1"],                       # [必需] 设备列表
    command=["show version"],                   # [可选] 查询命令（与 config 互斥）
    config=["hostname R1"],                    # [可选] 配置命令（与 command 互斥）
    mode="auto",                                # [可选] 执行模式：auto/exec/bulk
    ttl=300,                                    # [可选] 任务超时时间（秒）
    connection_args={},                         # [可选] 连接参数（覆盖默认值）
    driver="netmiko",                           # [可选] 驱动名称（覆盖默认值）
    driver_args={},                             # [可选] 驱动特定参数
    credential={},                              # [可选] Vault 凭据引用
    rendering={},                               # [可选] 模板渲染配置
    parsing={},                                 # [可选] 输出解析配置
    queue_strategy="fifo",                      # [可选] 队列策略：fifo/pinned
    result_ttl=3600,                            # [可选] 结果保留时间（秒）
    webhook={},                                 # [可选] Webhook 回调配置
    execution_timeout=None,                     # [可选] 命令执行超时（秒）
    detach=False,                               # [可选] 是否后台运行
    file_transfer=None,                         # [可选] 文件传输任务配置 (upload/download)
    push_interval=None,                         # [可选] Webhook 增量推送间隔 (秒)
    staged_file_id=None,                        # [可选] 暂存文件 ID (用于文件传输)
    local_upload_file=None,                     # [可选] 本地上传文件路径
    callback=None,                              # [可选] 进度回调函数 callback(JobProgress)
)
```

### 2.2 `collect()` 方法（只读查询）

```python
job = client.collect(
    devices=["10.1.1.1"],                       # [必需] 设备列表
    command=["show version"],                   # [必需] 查询命令
    ttl=300,                                    # [可选] 任务超时时间（秒）
    connection_args={},                         # [可选] 连接参数
    driver="netmiko",                           # [可选] 驱动名称
    driver_args={},                             # [可选] 驱动特定参数
    credential={},                              # [可选] Vault 凭据引用
    parsing={},                                 # [可选] 输出解析配置
    queue_strategy="fifo",                      # [可选] 队列策略
    result_ttl=3600,                            # [可选] 结果保留时间（秒，60-604800）
    webhook={},                                 # [可选] Webhook 回调配置
    execution_timeout=60,                       # [可选] 命令执行超时（秒）
    detach=False,                               # [可选] 是否后台运行
    callback=None,                              # [可选] 进度回调函数
)
```

### 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `devices` | `str` / `list` | ✅ | - | 设备列表，详见第 5 节 |
| `command` | `str` / `list` | ✅* | - | 查询命令（与 config 互斥） |
| `config` | `str` / `list` | ✅* | - | 配置命令（与 command 互斥） |
| `mode` | `str` | ❌ | `"auto"` | 执行模式：`auto`, `exec`, `bulk` |
| `ttl` | `int` | ❌ | `300` | 任务在队列中的超时时间（秒） |
| `execution_timeout` | `int` | ❌ | `None` | 单条命令实际执行的硬超时（秒） |
| `connection_args` | `dict` | ❌ | `{}` | 连接参数，会与客户端默认参数合并 |
| `driver` | `str` | ❌ | - | 驱动，覆盖客户端默认值 |
| `driver_args` | `dict` | ❌ | `None` | 驱动参数，优化执行性能 |
| `credential` | `dict` | ❌ | `None` | Vault 凭据配置，详见第 6 节 |
| `rendering` | `dict` | ❌ | `None` | 模板渲染配置，详见第 7 节 |
| `parsing` | `dict` | ❌ | `None` | 输出解析配置，详见第 8 节 |
| `file_transfer` | `dict` | ❌ | `None` | 文件传输配置：`{"operation": "upload", "remote_path": "..."}` |
| `staged_file_id` | `str` | ❌ | `None` | 已上传到服务器的暂存文件 ID |
| `push_interval` | `int` | ❌ | `None` | Webhook 增量推送日志的间隔时间（秒） |
| `detach` | `bool` | ❌ | `False` | 异步提交不等待结果，返回 `Job` 含 `task_id` |
| `callback` | `Callable` | ❌ | `None` | 流程进度回调，接收 `JobProgress` 对象 |

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
    "read_timeout": 60,             # [可选] 读取超时（秒），默认 60 (SDK 0.4.0+)
    "delay_factor": 3,              # [可选] 延迟因子，默认 3
    "max_loops": 5000,              # [可选] 最大循环次数，默认 5000
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

`devices` 参数支持多种格式，可以是单个设备或设备列表，也支持列表生成式、生成器等可迭代对象。

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

# 格式5：列表生成式（动态生成设备列表）
devices = [f"10.1.1.{i}" for i in range(1, 255)]  # 生成 10.1.1.1 到 10.1.1.254

# 格式6：任何可迭代对象（生成器、迭代器等）
devices = (f"10.154.254.{i}" for i in range(1, 117))  # 生成器表达式
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
    command="show version",  # base 命令
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

从 Vault 获取凭据（需要配置 Vault 集成）。`credential` 是一个独立的认证来源，与 `connection_args` 中的密码是**不同的层级**。

### 6.1 参数说明

```python
credential = {
    "name": "vault_kv",             # [必需] 后端配置的凭据提供者名称（provider name）
    "ref": "secret/data/network",   # [必需] Vault 密钥路径
    "mount": "kv",                  # [可选] Vault 挂载点，默认 "kv" 或后端配置的默认值
    "version": 1,                   # [可选] 版本号（用于版本化存储）
    "namespace": "ops",             # [可选] 命名空间或租户范围
    "field_mapping": {              # [可选] 字段映射（仅当 Vault 中的字段名与标准不同时需要）
        "username": "user",         # 将 Vault 中的 "user" 映射为 "username"
        "password": "pass",         # 将 Vault 中的 "pass" 映射为 "password"
    },
}
```

### 6.2 参数优先级

**重要**：如果同时提供 `credential` 和 `connection_args` 中的 `username`/`password`，**`credential` 会优先生效**，`connection_args` 中的认证信息会被覆盖。

**推荐做法**：使用 `credential` 时，在 `connection_args` 中**不要**提供 `username` 和 `password`，只提供其他连接参数（如 `device_type`、`port` 等）。

### 6.3 使用示例

```python
# 示例1：基本用法（Vault 中的字段名为标准名称）
job = client.collect(
    devices="10.1.1.1",
    command="show version",
    connection_args={
        "device_type": "cisco_ios",  # 只提供非认证参数
        # 不提供 username 和 password
    },
    credential={
        "ref": "secret/data/network/cisco",  # Vault 路径
        "mount": "kv",  # 可选，默认 "kv"
    },
)

# 示例2：字段映射（Vault 中的字段名不同）
job = client.collect(
    devices="10.1.1.1",
    command="show version",
    connection_args={
        "device_type": "hp_comware",
    },
    credential={
        "name": "vault_kv",  # 后端 provider 名称
        "ref": "netpulse/ops",  # Vault 路径
        "mount": "kv",
        "field_mapping": {  # 仅当字段名不同时需要
            "username": "cisco_user",
            "password": "cisco_pass",
        },
    },
)

# 示例3：不推荐 - 同时提供 credential 和 connection_args 中的密码
# credential 会覆盖 connection_args 中的认证信息
job = client.collect(
    devices="10.1.1.1",
    command="show version",
    connection_args={
        "device_type": "cisco_ios",
        "username": "admin",  # 会被 credential 覆盖
        "password": "oldpass",  # 会被 credential 覆盖
    },
    credential={
        "ref": "secret/data/network/cisco",  # 这个会生效
    },
)
```

---

## 7. rendering 模板渲染

使用 Jinja2 模板渲染命令或配置

```python
rendering = {
    "name": "jinja2",               # [必需] 渲染器名称，目前支持 "jinja2"
    "template": "show vlan {{ id }}", # [必需] 内联模板（Jinja2 语法）
    "context": {                    # [必需] 模板变量
        "id": 100,
        "name": "DATA",
    },
}
```

> [!IMPORTANT]
> 使用 `rendering` 时，`command` 或 `config` 参数**必须设置为空字典 `{}`**，API 会用渲染后的模板结果替换它。

### 7.1 查询命令示例

```python
job = client.collect(
    devices="10.1.1.1",
    command={},  # 使用模板时必须为空字典
    rendering={
        "name": "jinja2",
        "template": "show vlan {{ vlan_id }}",
        "context": {"vlan_id": 100},
    },
)
```

### 7.2 配置命令示例

```python
# 配置模板
config_template = """interface {{ interface }}
description {{ description }}
ip address {{ ip }} {{ mask }}"""

job = client.run(
    devices=["10.1.1.1", "10.1.1.2"],
    config={},  # 使用模板时必须为空字典
    rendering={
        "name": "jinja2",
        "template": config_template,
        "context": {
            "interface": "GigabitEthernet0/1",
            "description": "Uplink to Core",
            "ip": "192.168.1.1",
            "mask": "255.255.255.0",
        },
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
    "use_ntc_templates": True,      # [可选] 是否使用 ntc-templates
}
```

示例：
```python
job = client.collect(
    devices="10.1.1.1",
    command="show version",
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
    "name": "basic",                              # [可选] WebHook 处理器名称，默认 "basic"
    "url": "https://api.example.com/callback",    # [必需] 回调 URL
    "method": "POST",                             # [可选] HTTP 方法：GET/POST/PUT/DELETE/PATCH，默认 POST
    "headers": {                                  # [可选] 自定义 Headers
        "Authorization": "Bearer token",
        "Content-Type": "application/json",
    },
    "cookies": {                                  # [可选] Cookies
        "session": "xxx",
    },
    "auth": ("username", "password"),             # [可选] Basic Auth 认证
    "timeout": 5.0,                               # [可选] 回调超时（秒），范围 0.5-120，默认 5.0
}
```

示例：
```python
job = client.collect(
    devices="10.1.1.1",
    command="show version",
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
    command="show version",
)
```

### 示例2：慢速设备优化

```python
job = client.collect(
    devices="10.1.1.1",
    command="show running-config",
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
    command="show version",
)
```

### 示例5：使用 Vault 凭据

```python
job = client.collect(
    devices="10.1.1.1",
    command="show version",
    connection_args={
        "device_type": "cisco_ios",  # 只提供非认证参数
    },
    credential={
        "ref": "secret/data/network/cisco",
        "mount": "kv",  # 可选
    },
)
```

### 示例6：Webhook 通知

```python
job = client.collect(
    devices=["10.1.1.1", "10.1.1.2"],
    command="show version",
    webhook={
        "url": "https://api.example.com/notify",
    },
)
```

### 示例7：列表生成式生成设备列表

```python
# 动态生成设备 IP 列表
devices = [f"10.1.1.{i}" for i in range(1, 255)]

job = client.collect(
    devices=devices,
    command="show version",
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

## 10. Result 对象

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `job_id` | `str` | 任务 ID |
| `device_id` | `str` | 设备 IP/标识 |
| `device_name` | `str` | 设备名称 |
| `command` | `str` | 执行的命令 |
| `stdout` | `str` | 标准输出 |
| `stderr` | `str` | 标准错误输出 |
| `ok` | `bool` | 任务是否提交/执行成功 |
| `duration_ms` | `int` | 执行耗时（毫秒） |
| `duration_s` | `float` | 执行耗时（秒，property） |
| `exit_status` | `int` | 命令退出状态码 (0 为成功) |
| `download_url` | `str` | 文件下载链接 (仅限文件操作) |
| `error` | `Error` | 错误信息（`type`, `message`, `retryable`） |
| `metadata` | `dict` | 驱动返回的原始元数据 |
| `parsed` | `Any` | 结构化解析后的数据 |
| `is_success` | `bool` | 逻辑成功（`ok=True` 且无设备错误，property） |

### 方法

| 方法 | 返回 | 说明 |
|------|------|------|
| `has_device_error(patterns)` | `bool` | 检测输出是否有错误 |
| `get_error_lines()` | `List[str]` | 提取错误行 |
| `to_dict()` | `dict` | 转字典 |
| `to_json()` | `str` | 转 JSON |

---

## 11. Job 对象

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `id` | `str` | 任务 ID |
| `status` | `str` | 状态：`queued`/`started`/`finished`/`failed`/`canceled` |
| `task_id` | `str` | 异步任务 ID (当 `detach=True` 时有效) |
| `all_ok` | `bool` | 是否所有结果均成功 (ok=True) |
| `stdout` | `str` | 合并后的所有 stdout 输出 (property) |
| `stderr` | `str` | 合并后的所有 stderr 输出 (property) |
| `parsed` | `dict` | 所有解析后的数据 `{command: data}` (property) |
| `text` | `str` | 带标题的格式化输出 (property) |
| `failed_commands`| `list` | 失败的命令列表 (property) |
| `created_at` | `datetime`| 创建时间 |
| `started_at` | `datetime`| 开始执行时间 |
| `ended_at` | `datetime`| 结束执行时间 |
| `worker` | `str` | 执行该任务的 Worker 名称 |

### 方法

| 方法 | 返回 | 说明 |
|------|------|------|
| `wait(timeout)` | `Job` | 等待完成 |
| `refresh()` | `Job` | 刷新状态 |
| `cancel()` | `None` | 取消任务 |
| `results()` | `List[Result]` | 所有结果列表 |
| `succeeded()` | `List[Result]` | 成功的结果 |
| `failed()` | `List[Result]` | 失败的结果 |
| `truly_succeeded()` | `List[Result]` | 真正成功的结果 (无设备错误) |
| `device_errors()` | `List[Result]` | 包含设备错误的结果 |
| `progress()` | `JobProgress` | 获取详细进度对象 |
| `stream(poll_interval)` | `Iterator` | 流式返回结果 |
| `raise_on_error()` | `Job` | 如果有失败则抛出异常 (支持链式) |
| `summary()` | `str` | 获取一句话执行摘要 |
| `to_json()` | `str` | 转完整 JSON 字符串 |

### 迭代

```python
for result in job:           # 直接迭代
    print(result.stdout)

result = job[0]              # 索引访问
results = job["10.1.1.1"]    # 按设备名
```

---

## 12. 后台管理对象

管理 API (`list_workers`, `list_detached_tasks`) 不再返回裸字典，而是返回封装好的 Pydantic 模型，以支持更好的 IDE 自动补全。

### 12.1 WorkerInfo 对象

通过 `client.list_workers()` 返回。

| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | Worker 名称 (通常为 UUID 格式) |
| `status` | `str` | Worker 状态 (`idle`, `busy`, `suspended`) |
| `pid` | `int` | 进程 PID |
| `hostname` | `str` | 运行该 Worker 的宿主机名 |
| `queues` | `list` | 监听的队列列表 |
| `last_heartbeat` | `str` | 最后心跳时间 |
| `birth_at` | `str` | Worker 启动时间 |
| `successful_job_count` | `int` | 处理成功的任务数 |
| `failed_job_count` | `int` | 处理失败的任务数 |

### 12.2 DetachedTaskInfo 对象

通过 `client.list_detached_tasks()` 返回。

| 属性 | 类型 | 说明 |
|------|------|------|
| `task_id` | `str` | 远端脱机任务 ID |
| `command` | `list` | 启动的原始命令 |
| `host` | `str` | 设备 IP/主机名 |
| `driver` | `str` | 使用的驱动 |
| `status` | `str` | 任务状态 (`launching`, `running`, `completed`) |
| `push_interval` | `int` | 日志推送间隔设定 |
| `created_at` | `str` | 任务创建时间 |

> ℹ️ **注**：`get_detached_task("id")` 接口除了返回以上元数据外，还会额外包含任务的最近实时输出 `stdout`，因此该接口依旧返回 `dict`。

---

## 相关文档

- **完整示例**：`examples/README.md`
- **SDK 文档**：`README.md`
