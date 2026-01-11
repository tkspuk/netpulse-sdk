"""
Result 对象属性 - 常用属性

推荐使用方式：
- output: 获取输出（自动处理成功/失败）
- ok: 判断是否成功
- device_name: 设备名
"""
from netpulse_sdk import NetPulseClient

np = NetPulseClient(
    base_url="http://localhost:9000",
    api_key="your-api-key",
    driver="netmiko",
    default_connection_args={"device_type": "cisco_ios", "username": "admin", "password": "password"},
)

result = np.collect("10.1.1.1", "show version").first()

# === 推荐用法（简单） ===
print(f"设备: {result.device_name}")
print(f"成功: {result.ok}")
print(f"输出: {result.output}")  # 自动处理成功/失败

# === 其他常用属性 ===
print(f"任务ID: {result.job_id}")
print(f"命令: {result.command}")
print(f"耗时: {result.duration_ms} ms")

# === 高级用法（需要原始数据时） ===
# result.stdout   - 原始标准输出
# result.stderr   - 原始错误输出
# result.is_success - 任务成功且设备无错误
# result.has_device_error() - 检测设备输出中的错误
