"""
每设备不同命令 - 批量执行时覆盖命令
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import pyeapi_client as np

# 设备可带 command 字段覆盖 base 命令
switches = [
    "10.1.1.1",                                           # 使用 base 命令
    {"host": "10.1.1.2", "command": "show interfaces status"},
    {"host": "10.1.1.3", "command": "show vlan"},
    {"host": "10.1.1.4", "command": "show ip route"},
]

for result in np.collect(switches, "show version"):  # base 命令
    print(f"{result.device_name} 执行: {result.command}")
