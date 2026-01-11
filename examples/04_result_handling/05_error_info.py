"""
错误信息获取 - 详细错误处理
"""
from netpulse_sdk import NetPulseClient

np = NetPulseClient(
    base_url="http://localhost:9000",
    api_key="your-api-key",
    driver="netmiko",
    default_connection_args={"device_type": "cisco_ios", "username": "admin", "password": "password"},
)

job = np.collect(["10.1.1.1", "10.1.1.2"], "show version")

# 遍历失败的结果
for result in job.failed():
    print(f"=== {result.device_name} ===")
    
    # error 对象属性
    if result.error:
        print(f"错误类型: {result.error.type}")
        print(f"错误信息: {result.error.message}")
    
    # stderr 标准错误输出
    if result.stderr:
        print(f"标准错误: {result.stderr}")
