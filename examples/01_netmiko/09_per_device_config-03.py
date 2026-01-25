"""
每设备不同配置 - config 覆盖
"""
from connection import np

# 设备可带 config 字段覆盖 base 配置
devices = [
    {
        "host": "10.210.253.18",
        "config": ["interface vlan 51", "description specific_config_18"],
    },
    {
        "host": "10.210.253.19",
        "config": ["interface vlan 52", "description specific_config_19"],
    },
    # 其他设备可以使用简单字符串，将使用 base_config
    "10.210.253.20",
]

base_config = [
    "interface vlan 51",
    "packet-filter 3005 inbound",
    "save f",
]

# 混合模式：有的设备用 base_config，有的用自己的 config
job = np.run(devices=devices, config=base_config)

for result in job:
    print(f"设备 {result.device_name} 配置结果: {result.ok}")
    if not result.ok:
        print(f"错误: {result.error}")
