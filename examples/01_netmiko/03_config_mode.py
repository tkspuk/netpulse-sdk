"""
配置模式推送 - 进入配置模式执行命令
"""
from connection import np

# 使用 config 参数会自动进入配置模式
config_commands = [
    "interface GigabitEthernet0/1",
    "description WAN-Link",
    "ip address 192.168.1.1 255.255.255.0",
    "no shutdown",
]

job = np.run(devices="10.1.1.1", config=config_commands)
print(f"配置成功: {job.all_ok}")
