"""
服务管理 - systemctl 操作
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import paramiko_client as np

server = "10.1.1.1"

# 查看服务状态
result = np.collect(server, "systemctl status nginx")[0]
print(result.stdout)

# 查看所有运行中的服务
result = np.collect(server, "systemctl list-units --type=service --state=running")[0]
print(result.stdout)

# 重启服务（使用 run 进行变更操作）
job = np.run(devices=server, config="systemctl restart nginx")
print(f"重启成功: {job.all_ok}")
