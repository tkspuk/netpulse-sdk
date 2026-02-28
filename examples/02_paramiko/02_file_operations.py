"""
文件操作 - 查看、搜索、统计
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import paramiko_client as np

# 查看文件
result = np.collect("10.1.1.35", "cat /etc/hosts")[0]
print(result.stdout)

# 搜索文件内容
result = np.collect("10.1.1.35", "grep -r 'error' /var/log/")[0]
print(result.stdout)

# 目录列表
result = np.collect("10.1.1.35", "ls -la /var/log/")[0]
print(result.stdout)

# 磁盘使用
result = np.collect("10.1.1.35", "df -h")[0]
print(result.stdout)
