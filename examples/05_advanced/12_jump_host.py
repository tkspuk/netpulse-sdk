"""
通过跳板机 (Jump Host) 连接 - 网络/服务器运维常见场景
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import np

# 场景：目标设备 10.1.1.1 无法直接访问，需要通过跳板机 10.1.1.254 进行 SSH 隧道连接

# --- 方式 1: Netmiko 驱动 (通过 sock 参数) ---
# Netmiko 使用 sock 参数来处理代理连接，通常需要配合 Paramiko 的 SSHClient
# 注意：这需要本地有相应的 SSH 隧道或 proxy 命令
job = np.run(
    devices="10.1.1.1",
    command="show version",
    connection_args={
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "password",
        # Netmiko 驱动的高级连接参数
        "driver_args": {
            "ssh_config_file": "~/.ssh/config",  # 使用本地 ssh config 中的 ProxyJump 设置
            "use_keys": True
        }
    }
)

# --- 方式 2: Paramiko 驱动 (通过 ProxyCommand) ---
# 适用于 Linux 服务器，直接在 driver_args 中注入代理指令
from connection import paramiko_client
job_server = paramiko_client.run(
    devices="10.1.1.10",
    command="uptime",
    driver_args={
        # 相当于 ssh -o ProxyCommand="ssh -W %h:%p user@jump-host"
        "proxy_command": "ssh -W %h:%p ops@10.1.1.254"
    }
)

print("跳板机示例 - 展示了如何配置代理连接")
