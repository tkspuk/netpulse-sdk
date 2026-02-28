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
    print(f"[OK] {result.device_name}: {result.stdout[:50]}...")

# failed() - 任务失败（连接失败、超时等）
for result in job.failed():
    print(f"[FAIL] {result.device_name}: {result.stderr}")

# === 快捷检查 ===
if job.all_ok:
    print("所有设备成功!")
else:
    print(f"失败设备: {len(list(job.failed()))} 个")

# === 进阶过滤 - 区分业务层面的确切成功 ===

# truly_succeeded() - 任务完成 且 回显中没有 "Invalid command" 等错误指标
print(f"真正成功的数量: {len(job.truly_succeeded())}")

# device_errors() - 任务虽然完成（连接没断），但设备回显了错误提示
for result in job.device_errors():
    print(f"[DEVICE ERROR] {result.device_name}: {result.get_error_lines()}")
