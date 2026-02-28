"""
基础命令 - Linux 系统信息
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import paramiko_client as np

# 单条命令
result = np.collect("10.1.1.35", "uname -a")[0]
print(result.ok)
print(result.stdout)

# 多条命令
result = np.collect("10.1.1.35", ["hostname", "uptime", "free -h"])[0]
print(result.ok)
print(result.stdout)
