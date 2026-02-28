"""
每设备不同命令 - command 覆盖
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import np

# 设备可带 command 字段覆盖 base 命令
devices = [
    "10.1.1.1",                                    # 使用 base 命令
    {"host": "10.1.1.2", "command": "show power"},
    {"host": "10.1.1.3", "command": "show environment"},
]

for result in np.collect(devices, "show version"):  # base 命令
    print(f"{result.device_name} 执行: {result.command}")
