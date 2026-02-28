"""
批量设备使用不同凭据 - single run with multiple credentials
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import np

# 场景：一次性下发任务到多台设备，但这些设备的账号/驱动可能各不相同
# devices 参数支持传入 Dict 列表，每个字典可以包含独立的连接信息
devices = [
    {
        "host": "10.1.1.1",
        "driver": "netmiko",
        "connection_args": {"device_type": "cisco_ios", "username": "admin1", "password": "pass1"},
    },
    {
        "host": "10.1.1.2",
        "driver": "netmiko",
        "connection_args": {"device_type": "hp_comware", "username": "admin2", "password": "pass2"},
    },
    {
        "host": "10.1.1.3",
        "credential": {"ref": "vault/secret/key-01"}, # 也可以混合使用 Vault 凭据引用
    }
]

# 统一执行
job = np.run(
    devices=devices,
    command="display version"
)

# 或者是通过模式匹配 (mode="bulk")
# np.run(devices=devices, command="...", mode="bulk")

for result in job:
    print(f"设备 {result.device_name} ({result.metadata.get('host')}) => {result.ok}")
