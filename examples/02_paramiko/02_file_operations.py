"""
文件操作 - 查看、搜索、统计
"""
from connection import np

# 查看文件
result = np.collect("10.1.1.1", "cat /etc/hosts").first()
print(result.stdout)

# 搜索文件内容
result = np.collect("10.1.1.1", "grep -r 'error' /var/log/").first()
print(result.stdout)

# 目录列表
result = np.collect("10.1.1.1", "ls -la /var/log/").first()
print(result.stdout)

# 磁盘使用
result = np.collect("10.1.1.1", "df -h").first()
print(result.stdout)
