"""
快捷访问 - first() / all_ok / outputs
"""
from netpulse_sdk import NetPulseClient

np = NetPulseClient(
    base_url="http://localhost:9000",
    api_key="your-api-key",
    driver="netmiko",
    default_connection_args={"device_type": "cisco_ios", "username": "admin", "password": "password"},
)

# === first() - 获取第一个结果 ===
result = np.collect("10.1.1.1", "show version").first()
print(result.stdout)

# === all_ok - 判断是否全部成功 ===
job = np.collect(["10.1.1.1", "10.1.1.2"], "show version")
if job.all_ok:
    print("全部成功！")
else:
    print(f"失败数: {len(job.failed())}")

# === outputs - 获取输出字典 ===
outputs = job.outputs  # {"device": "output"}
for device, output in outputs.items():
    print(f"{device}: {len(output)} 字符")
