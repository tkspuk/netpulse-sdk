"""
队列策略 - FIFO vs Pinned
"""
from netpulse_sdk import NetPulseClient, QueueStrategy

np = NetPulseClient(
    base_url="http://localhost:9000",
    api_key="your-api-key",
    driver="netmiko",
    default_connection_args={"device_type": "cisco_ios", "username": "admin", "password": "password"},
)

# === FIFO 策略（默认） ===
# 先进先出，每次新建连接，适合一次性任务
job = np.collect(
    devices="10.1.1.1",
    command="show version",
    queue_strategy=QueueStrategy.FIFO,  # 或 "fifo"
)

# === Pinned 策略 ===
# 固定 Worker，复用连接，适合同设备频繁操作
job = np.collect(
    devices="10.1.1.1",
    command="show version",
    queue_strategy=QueueStrategy.PINNED,  # 或 "pinned"
)

print(f"成功: {job.all_ok}")
