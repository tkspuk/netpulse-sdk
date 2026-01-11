"""
服务管理 - systemctl 操作
"""
from connection import np

server = "10.1.1.1"

# 查看服务状态
result = np.collect(server, "systemctl status nginx").first()
print(result.stdout)

# 查看所有运行中的服务
result = np.collect(server, "systemctl list-units --type=service --state=running").first()
print(result.stdout)

# 重启服务（使用 run 进行变更操作）
job = np.run(devices=server, config="systemctl restart nginx")
print(f"重启成功: {job.all_ok}")
