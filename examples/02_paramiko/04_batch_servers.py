"""
批量服务器 - 大规模 Linux 运维
"""
from connection import np

# 服务器列表
servers = [f"10.1.1.{i}" for i in range(1, 101)]

# 批量采集系统信息
job = np.collect(servers, ["hostname", "uptime"])

print(f"成功: {len(job.succeeded())}")
print(f"失败: {len(job.failed())}")

# 获取所有输出
for device, output in job.outputs.items():
    print(f"{device}: {output[:50]}...")
