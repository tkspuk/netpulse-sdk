"""
Webhook 回调 - 任务完成后通知
"""
from netpulse_sdk import NetPulseClient

np = NetPulseClient(
    base_url="http://localhost:9000",
    api_key="your-api-key",
    driver="netmiko",
    default_connection_args={"device_type": "cisco_ios", "username": "admin", "password": "password"},
)

job = np.collect(
    devices="10.1.1.1",
    command="show version",
    webhook={
        "url": "https://api.example.com/callback",
        "method": "POST",                # GET/POST/PUT/DELETE/PATCH
        "headers": {
            "Authorization": "Bearer your-token",
            "Content-Type": "application/json",
        },
        "cookies": {"session": "xxx"},   # 可选
        "auth": ("user", "pass"),        # 可选: Basic Auth
        "timeout": 10.0,                 # 请求超时（0.5-120秒）
    },
).first()

print(result.stdout)
