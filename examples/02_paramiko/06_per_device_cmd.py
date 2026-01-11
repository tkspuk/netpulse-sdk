"""
每设备不同命令 - 批量执行时覆盖命令
"""
from connection import np

# 设备可带 command 字段覆盖 base 命令
servers = [
    "10.1.1.1",                                      # 使用 base 命令
    {"host": "10.1.1.2", "command": "df -h"},        # 查看磁盘
    {"host": "10.1.1.3", "command": "free -h"},      # 查看内存
    {"host": "10.1.1.4", "command": "top -bn1 | head -20"},  # 查看进程
]

for result in np.collect(servers, "uname -a"):  # base 命令
    print(f"{result.device_name} 执行: {result.command}")
    print(result.stdout[:100])
