"""
Result 序列化 - to_dict() / to_json()
"""
from netpulse_sdk import NetPulseClient

np = NetPulseClient(
    base_url="http://localhost:9000",
    api_key="your-api-key",
    driver="netmiko",
    default_connection_args={"device_type": "cisco_ios", "username": "admin", "password": "password"},
)

result = np.collect("10.1.1.1", "show version").first()

# 转为字典
data = result.to_dict()
print(data)
# {'job_id': '...', 'device_name': '10.1.1.1', 'stdout': '...', 'ok': True, ...}

# 转为 JSON 字符串
json_str = result.to_json()
print(json_str)
