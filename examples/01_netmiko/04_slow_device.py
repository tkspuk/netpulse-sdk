"""
慢速设备优化 - driver_args 参数详解
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import np

# driver_args 透传给 Netmiko，常用参数：
job = np.collect(
    devices="10.1.1.1",
    command="show running-config",
    ttl=600,             # [可选] 任务在队列中的存活时间 (秒)
    execution_timeout=120, # [建议] 任务最长运行时间 (秒)
    driver_args={
        "read_timeout": 60,     # 读取超时（秒），默认 10
        "delay_factor": 2,      # 延迟因子，增大可解决慢速设备
        "global_delay_factor": 2,  # 全局延迟因子
    },
)

# 打印整体输出
print(job.stdout)
