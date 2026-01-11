"""
连接配置模板

支持两种方式:
1. 显式传参
2. 环境变量: NETPULSE_URL, NETPULSE_API_KEY
"""
from netpulse_sdk import NetPulseClient

# # ============ 方式1: 显式传参 ============
# np = NetPulseClient(
#     base_url="http://localhost:9000",
#     api_key="your-api-key",
#     driver="netmiko",
#     default_connection_args={
#         "device_type": "cisco_ios",
#         "username": "admin",
#         "password": "password",
#     },
# )

# ============ 方式2: 环境变量 ============
# export NETPULSE_URL=http://localhost:9000
# export NETPULSE_API_KEY=your-api-key
#
np = NetPulseClient(
    driver="netmiko",
    default_connection_args={
        "device_type": "hp_comware",
        "username": "admin",
        "password": "password",
    },
)
