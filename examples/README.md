# NetPulse SDK 示例

> ⚠️ **注意**：示例仅供参考学习，请勿直接在生产环境执行

---

## 目录结构

```
examples/
├── 00_quickstart/         # 快速入门（通用）
├── 01_netmiko/            # Netmiko 驱动（网络设备）
├── 02_paramiko/           # Paramiko 驱动（Linux 服务器）
├── 03_pyeapi/             # PyEAPI 驱动（Arista）
├── 04_result_handling/    # 结果处理专题
└── 05_advanced/           # 高级用法
```

---

## 快速入门

```python
from netpulse_sdk import NetPulseClient

np = NetPulseClient(
    base_url="http://localhost:9000",
    api_key="your-api-key",
    driver="netmiko",
    default_connection_args={
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "password",
    },
)

# 查询
for result in np.collect("10.1.1.1", "show version"):
    print(result.stdout)  # 直接获取标准输出

# 配置
job = np.run(devices="10.1.1.1", config="hostname ROUTER-01")
print(f"成功: {job.all_ok}")
```

---

## 推荐用法

### Result 对象

```python
result = np.collect("10.1.1.1", "show version")[0]

# ✅ 推荐使用
result.stdout       # 标准输出内容
result.ok           # 是否成功
result.device_name  # 设备名
result.job_id       # 作业 ID（存数据库用）

# 序列化
result.to_dict()    # 转字典
result.to_json()    # 转 JSON
```

### Job 对象

```python
job = np.collect(["10.1.1.1", "10.1.1.2"], "show version")

# ✅ 推荐使用
job.all_ok          # 所有设备都成功
job[0]              # 第一个结果 (Result 对象)
job.succeeded()     # 任务执行成功的 Result 列表
job.truly_succeeded() # 任务成功且回显无错误的 Result 列表
job.device_errors() # 任务成功但回显包含错误的 Result 列表
job.stdout          # {设备名: 输出} 字典 (如果是单条命令，Job.stdout 直接返回字符串)
job.stderr          # 错误输出字典
job.parsed          # 解析后的结构化数据字典
```

---

## 按驱动选择

| 驱动 | 适用场景 | 目录 |
|-----|---------|------|
| **Netmiko** | 网络设备（Cisco、华为、H3C等） | `01_netmiko/` |
| **Paramiko** | Linux 服务器运维 | `02_paramiko/` |
| **PyEAPI** | Arista 交换机（JSON输出） | `03_pyeapi/` |

---

## 示例索引

### 00_quickstart - 快速入门
| 文件 | 说明 |
|------|------|
| `connection.py` | 连接配置模板 |
| `01_single_query.py` | 单设备查询（多种写法） |
| `02_batch_query.py` | 批量查询（多种写法） |
| `03_config_push.py` | 配置推送 |

### 01_netmiko - 网络设备
| 文件 | 说明 |
|------|------|
| `01_basic_query.py` | 基础查询 |
| `02_multi_commands.py` | 多命令执行 |
| `03_config_mode.py` | 配置模式推送 |
| `04_slow_device.py` | 慢速设备优化（driver_args） |
| `05_multi_vendor.py` | 混合厂商（device_type覆盖） |
| `06_per_device_cmd.py` | 每设备不同命令 |
| `07_batch_config.py` | 批量配置下发 (含本地覆盖) |
| `10_template_config.py` | 模板生成配置 |

### 02_paramiko - Linux 服务器
| 文件 | 说明 |
|------|------|
| `01_basic_command.py` | 基础命令 |
| `02_file_operations.py` | 文件操作 |
| `03_service_manage.py` | 服务管理 |
| `04_batch_servers.py` | 批量服务器 |
| `05_ssh_key_auth.py` | SSH 密钥认证 |
| `06_per_device_cmd.py` | 每设备不同命令 |
| `07_long_running_task.py` | 长耗时任务 (wait/callback) |
| `08_detached_task.py` | 后台脱机任务 (Detached) |
| `09_file_transfer.py` | 文件传输 (upload/download) |
| `10_sudo_execution.py` | Sudo 执行 |
| `11_interactive_expect.py` | 交互式应答 (expect_map) |
| `12_environment_variables.py` | 环境变量注入 |
| `13_working_directory.py` | 工作目录切换 |
| `14_script_execution.py` | 脚本代码执行 (script_content) |
| `15_output_parsing.py` | 输出自动解析 (TextFSM) |
| `16_webhook_notify.py` | 任务完成后 Webhook 回调 |

### 03_pyeapi - Arista
| 文件 | 说明 |
|------|------|
| `01_json_output.py` | JSON 格式输出 |
| `02_structured_data.py` | 结构化数据查询 |
| `03_batch_config.py` | 批量配置 |
| `04_per_device_cmd.py` | 每设备不同命令 |

### 04_result_handling - 结果处理
| 文件 | 说明 |
|------|------|
| `01_iterate_results.py` | 迭代结果（多种写法） |
| `02_filter_results.py` | 过滤结果（succeeded/failed） |
| `03_quick_access.py` | 快捷访问（[0]/all_ok/outputs） |
| `04_result_attributes.py` | Result 对象属性 |
| `05_error_info.py` | 错误信息获取 |
| `06_serialization.py` | 序列化（to_dict/to_json） |

### 05_advanced - 高级用法
| 文件 | 说明 |
|------|------|
| `01_vault_credential.py` | Vault 凭据 |
| `02_webhook_callback.py` | Webhook 回调 |
| `03_template_render.py` | 模板渲染（内联/外部文件） |
| `04_queue_strategy.py` | 队列策略 |
| `05_context_manager.py` | Context Manager（with 语句） |
| `06_debug_mode.py` | 调试模式 |
| `07_template_parse.py` | 输出解析（TextFSM/ntc-templates） |
| `08_connection_test.py` | 🆕 设备连接测试 |
| `09_job_management.py` | 🆕 作业管理（查询/取消） |
| `10_worker_management.py` | 🆕 Worker 管理 |
| `11_config_file.py` | 🆕 配置文件使用 |
| `12_jump_host.py` | 🆕 跳板机 (Jump Host) |
| `13_custom_credentials.py` | 🆕 批量设备不同凭据 |
| `14_retry_handling.py` | 🆕 错误处理与重试 |

---

## 更多文档

- [参数参考](../docs/PARAMETERS_REFERENCE.md)
