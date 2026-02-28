"""
Result 对象属性 - 常用属性

推荐使用方式：
- stdout: 获取标准输出 (对应 API 字段)
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

result = np.collect("10.1.1.1", "show version")[0]

# === 推荐用法（简单） ===
print(f"设备: {result.device_name}")
print(f"成功: {result.ok}")
print(f"标准输出: {result.stdout}")  # 对应 API 0.4.0+ 字段

# === 其他常用属性 ===
print(f"任务ID: {result.job_id}")
print(f"命令: {result.command}")
print(f"耗时: {result.duration_ms} ms")

# === 高级用法（需要原始数据时） ===
# result.stdout   - 原始标准输出 (API 字段)
# result.stderr   - 原始错误输出 (API 字段)
# result.parsed   - 解析后的结构化数据
# result.exit_status - 命令退出状态码
# result.download_url - 文件下载地址 (针对文件传输任务)
# result.is_success  - 任务成功且回显无错误指标
# result.has_device_error() - 检测回显中的特定错误 (如 "Invalid input")
