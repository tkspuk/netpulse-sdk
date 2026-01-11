"""
基础命令 - Linux 系统信息
"""
from connection import np

# 单条命令
result = np.collect("10.155.30.35", "uname -a").first()
print(result.stdout)

# 多条命令
result = np.collect("10.155.30.35", ["hostname", "uptime", "free -h"]).first()
print(result.stdout)
