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
    print(result.output)  # 推荐：自动处理成功/失败

# 配置
job = np.run(devices="10.1.1.1", config="hostname ROUTER-01")
print(f"成功: {job.all_ok}")
```

---

## 推荐用法

### Result 对象

```python
result = np.collect("10.1.1.1", "show version").first()

# ✅ 推荐使用
result.output       # 输出内容（成功返回stdout，失败返回[ERROR]+stderr）
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
job.first()         # 第一个结果
job.succeeded()     # 成功的结果
job.failed()        # 失败的结果
job.outputs         # {设备名: 输出} 字典
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

### 02_paramiko - Linux 服务器
| 文件 | 说明 |
|------|------|
| `01_basic_command.py` | 基础命令 |
| `02_file_operations.py` | 文件操作 |
| `03_service_manage.py` | 服务管理 |
| `04_batch_servers.py` | 批量服务器 |
| `05_ssh_key_auth.py` | SSH 密钥认证 |
| `06_per_device_cmd.py` | 每设备不同命令 |
| `07_long_running_task.py` | 长时间任务（异步提交/状态轮询） |

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
| `03_quick_access.py` | 快捷访问（first/all_ok/outputs） |
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

---

## 更多文档

- [参数参考](../docs/PARAMETERS_REFERENCE.md)
