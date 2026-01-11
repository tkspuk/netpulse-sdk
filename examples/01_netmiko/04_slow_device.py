"""
慢速设备优化 - driver_args 参数详解
"""
from connection import np

# driver_args 透传给 Netmiko，常用参数：
result = np.collect(
    devices="10.1.1.1",
    command="show running-config",
    ttl=600,  # 任务超时 10 分钟
    driver_args={
        "read_timeout": 120,    # 读取超时（秒），默认 10
        "delay_factor": 2,      # 延迟因子，增大可解决慢速设备
        "fast_cli": False,      # 禁用快速模式（更稳定）
        "global_delay_factor": 2,  # 全局延迟因子
    },
).first()

print(result.stdout)
