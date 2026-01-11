"""
批量设备查询 - 展示多种写法
"""
from connection import np

devices = ["10.154.254.1", "10.154.254.2", "10.154.254.3"]

# === 写法1: for 循环迭代 ===
for result in np.collect(devices, "display version"):
    print(f"{result.device_name}: {result.ok}")

# === 写法2: outputs 属性获取字典 ===
outputs = np.collect(devices, "display version").outputs
for device, output in outputs.items():
    print(f"{device}: {output[:50]}...")

# === 写法3: all_ok 快速判断 ===
job = np.collect(devices, "display version")
print(f"全部成功: {job.all_ok}")
