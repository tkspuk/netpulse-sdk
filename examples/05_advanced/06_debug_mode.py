"""
调试模式 - 开启详细日志
"""
from netpulse_sdk import NetPulseClient, enable_debug

# 一行开启调试日志
enable_debug()

np = NetPulseClient(
    base_url="http://localhost:9000",
    api_key="your-api-key",
    driver="netmiko",
    default_connection_args={"device_type": "cisco_ios", "username": "admin", "password": "password"},
)

# 执行操作时会输出详细日志
result = np.collect("10.1.1.1", "show version").first()
print(result.stdout)
