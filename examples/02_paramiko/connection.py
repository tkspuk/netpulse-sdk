"""
Paramiko 驱动连接配置 - Linux 服务器
"""
from netpulse_sdk import NetPulseClient

BASE_URL = "http://your-base-url:9000"
API_KEY = "your-api-key"

np = NetPulseClient(
    base_url=BASE_URL,
    api_key=API_KEY,
    driver="paramiko",
    default_connection_args={
        "username": "root",
        "password": "your-password",
        # "port": 22,  # 可选，默认 22
    },
)
