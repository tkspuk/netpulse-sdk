"""
配置文件使用 - 从 netpulse.yaml 加载配置

新增功能 (P4)

配置文件搜索顺序:
1. 当前目录 netpulse.yaml
2. ~/.netpulse/config.yaml
"""
from netpulse_sdk import NetPulseClient

# === 方式1: 自动加载配置文件 ===
# 会自动查找 netpulse.yaml 并读取 default profile
# client = NetPulseClient()

# === 方式2: 指定 profile ===
# client = NetPulseClient(profile="production")

# === 方式3: 指定配置文件路径 ===
# client = NetPulseClient(config_path="/path/to/config.yaml")

# === 方式4: 混合使用（参数优先级更高）===
# 参数 > 配置文件 > 环境变量
# client = NetPulseClient(
#     driver="paramiko",  # 覆盖配置文件中的 driver
# )

# === 配置文件示例 ===
"""
# netpulse.yaml
default:
  base_url: http://localhost:9000
  api_key: ${NETPULSE_API_KEY}   # 支持环境变量引用
  driver: netmiko
  connection_args:
    device_type: hp_comware
    username: ops
    password: ${DEVICE_PASSWORD}

profiles:
  production:
    base_url: https://netpulse.company.com
    api_key: ${NETPULSE_PROD_API_KEY}
"""

print("配置文件示例 - 请查看源代码注释")
