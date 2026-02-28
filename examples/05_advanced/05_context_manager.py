"""
Context Manager - with 语句自动管理连接
"""
from netpulse_sdk import NetPulseClient

# 使用 with 语句，自动关闭连接池
with NetPulseClient(
    base_url="http://localhost:9000",
    api_key="your-api-key",
    driver="netmiko",
    default_connection_args={"device_type": "cisco_ios", "username": "admin", "password": "password"},
) as client:
    # 健康检查
    client.ping()
    
    # 执行操作
    result = client.collect("10.1.1.1", "show version")[0]
    print(result.stdout)

# 退出 with 块后自动调用 client.close()
