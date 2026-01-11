"""
过滤结果 - 成功/失败分类

推荐使用方式：
- succeeded(): 任务成功的结果
- failed(): 任务失败的结果
"""
from netpulse_sdk import NetPulseClient

np = NetPulseClient(
    base_url="http://localhost:9000",
    api_key="your-api-key",
    driver="netmiko",
    default_connection_args={"device_type": "cisco_ios", "username": "admin", "password": "password"},
)

job = np.collect(["10.1.1.1", "10.1.1.2", "10.1.1.3"], "show version")

# === 推荐用法（简单） ===

# succeeded() - 任务成功完成
for result in job.succeeded():
    print(f"[OK] {result.device_name}: {result.output[:50]}...")

# failed() - 任务失败（连接失败、超时等）
for result in job.failed():
    print(f"[FAIL] {result.device_name}: {result.output}")

# === 快捷检查 ===
if job.all_ok:
    print("所有设备成功!")
else:
    print(f"失败设备: {len(list(job.failed()))} 个")

# === 高级用法 ===
# 如需区分"任务成功但设备返回错误"的情况：
# for result in job.device_errors():
#     print(f"设备错误: {result.device_name}")
