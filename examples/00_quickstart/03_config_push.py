"""
配置推送
"""
from connection import np

# 单条配置
job = np.run(devices="10.1.1.1", config="hostname ROUTER-01")
print(f"成功: {job.all_ok}")

# 多条配置
job = np.run(
    devices="10.1.1.1",
    config=["interface GigabitEthernet0/1", "description WAN-Link"],
)
print(f"成功: {job.all_ok}")
