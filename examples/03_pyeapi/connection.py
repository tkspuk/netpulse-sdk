"""
PyEAPI 驱动连接配置 - Arista 交换机
"""
from netpulse_sdk import NetPulseClient

BASE_URL = "http://localhost:9000"
API_KEY = "your-api-key"

np = NetPulseClient(
    base_url=BASE_URL,
    api_key=API_KEY,
    driver="pyeapi",
    default_connection_args={
        "username": "admin",
        "password": "password",
        # "transport": "https",  # 可选: http, https
        # "port": 443,
    },
)
