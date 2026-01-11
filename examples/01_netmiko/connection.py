"""
Netmiko 驱动连接配置 - 网络设备

支持环境变量: NETPULSE_URL, NETPULSE_API_KEY
"""
from netpulse_sdk import NetPulseClient

# 使用环境变量或显式传参
np = NetPulseClient(
    driver="netmiko",
    default_connection_args={
        "device_type": "hp_comware",  # cisco_ios, hp_comware, huawei 等
        "username": "admin",
        "password": "password",
    },
)
