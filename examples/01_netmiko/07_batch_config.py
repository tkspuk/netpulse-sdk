"""
每设备不同配置 - config 覆盖

⚠️ 危险：此示例涉及设备配置变更。
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import np

# 场景：批量下发配置，但其中几台需要特定的描述或设置来覆盖通用配置
devices = [
    {
        "host": "10.1.1.1",
        "config": ["interface Vlan 1", "description [Region-A] Core-SW"],
    },
    {
        "host": "10.1.1.2",
        "config": ["interface Vlan 1", "description [Region-B] Dist-SW"],
    },
    # 也可以混合使用字符串，这些设备将使用下面的 base_config
    "10.1.1.3",
    "10.1.1.4",
]

# 通用基础配置（当设备没有提供自己的 config 时使用）
base_config = [
    "interface Vlan 1",
    "description default-netpulse-description",
]

# 混合模式执行
job = np.run(devices=devices, config=base_config)

for result in job:
    print(f"设备 {result.device_name} 配置结果: {result.ok}")
    if not result.ok:
        print(f"错误: {result.error}")
