"""
迭代结果 - 多种写法对比
"""
from netpulse_sdk import NetPulseClient

np = NetPulseClient(
    base_url="http://localhost:9000",
    api_key="your-api-key",
    driver="netmiko",
    default_connection_args={"device_type": "cisco_ios", "username": "admin", "password": "password"},
)

devices = ["10.1.1.1", "10.1.1.2"]
job = np.collect(devices, "show version")

# === 写法1: for 循环（最通用） ===
for result in job:
    print(f"{result.device_name}: {result.ok}")

# === 写法2: [0] 索引访问（推荐） ===
result = job[0]
print(result.stdout)

# === 写法3: stdout 获取字典 ===
stdout_dict = job.stdout  # {"10.1.1.1": "output1", "10.1.1.2": "output2"}
print(stdout_dict)

# === 写法4: to_dict() 按设备分组 ===
data = job.to_dict()  # {"10.1.1.1": [Result, ...], "10.1.1.2": [Result, ...]}
print(data)
