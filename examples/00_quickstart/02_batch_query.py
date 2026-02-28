"""
批量设备查询 - 展示多种写法
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import np

devices = ["10.1.1.1", "10.1.1.2", "10.1.1.3"]

# === 写法1: for 循环迭代 ===
for result in np.collect(devices, "display version"):
    print(f"{result.device_name}: {result.ok}")

# === 写法2: stdout 属性针对 JobGroup 返回 {device: consolidated_stdout} 字典 ===
stdout_dict = np.collect(devices, "display version").stdout
for device, output in stdout_dict.items():
    print(f"{device}: {output.strip()[:50]}...")

# === 写法3: all_ok 快速判断 ===
job = np.collect(devices, "display version")
print(f"全部成功: {job.all_ok}")
