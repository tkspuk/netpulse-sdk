"""
配置模式推送 - 进入配置模式执行命令
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import np

# 使用 config 参数会自动进入配置模式
config_commands = [
    "interface Vlan-interface 3888",
    "description netpulse-sdk-test",
    "mtu 12341",
    "ip address 192.168.1.1 255.255.255.0",
]

# enable_mode=True: 执行前进入特权模式 (Netmiko)
# save=True: 执行完成后自动保存配置 (Netmiko write memory)
job = np.run(
    devices="10.1.1.1", 
    config=config_commands, 
    save=True
)
print(f"配置成功状态: {job.all_ok}")

# print("stdout: ",job.stdout)
print("stderr: \n",job.stderr)

