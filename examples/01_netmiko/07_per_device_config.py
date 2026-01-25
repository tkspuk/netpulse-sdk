"""
每设备不同配置 - config 覆盖
"""
from connection import np

# 设备可带 config 字段覆盖 base 配置
devices = [
    {
        "host": "10.210.253.18",
        "config": [
            "undo int vlan 51",
            "undo int vlan 52",
            "int vlan 51",
            "ip add 26.212.128.254 24",
            "save f",
        ],
    },
    {
        "host": "10.210.253.19",
        "config": [
            "undo int vlan 53",
            "undo int vlan 54",
            "int vlan 51",
            "ip add 26.212.129.254 24",
            "save f",
        ],
    },
    {
        "host": "10.210.253.20",
        "config": [
            "undo int vlan 55",
            "undo int vlan 56",
            "int vlan 51",
            "ip add 26.212.130.254 24",
            "save f",
        ],
    },
    {
        "host": "10.210.253.21",
        "config": [
            "undo int vlan 57",
            "undo int vlan 58",
            "int vlan 51",
            "ip add 26.212.131.254 24",
            "save f",
        ],
    },
    {
        "host": "10.210.253.34",
        "config": [
            "undo int vlan 51",
            "undo int vlan 52",
            "int vlan 51",
            "ip add 26.212.144.254 24",
            "save f",
        ],
    },
    {
        "host": "10.210.253.35",
        "config": [
            "undo int vlan 53",
            "undo int vlan 54",
            "int vlan 51",
            "ip add 26.212.145.254 24",
            "save f",
        ],
    },
    {
        "host": "10.210.253.36",
        "config": [
            "undo int vlan 55",
            "undo int vlan 56",
            "int vlan 51",
            "ip add 26.212.146.254 24",
            "save f",
        ],
    },
    {
        "host": "10.210.253.37",
        "config": [
            "undo int vlan 57",
            "undo int vlan 58",
            "int vlan 51",
            "ip add 26.212.147.254 24",
            "save f",
        ],
    },
]

base_config = [

]

# 混合模式：有的设备用 base_config，有的用自己的 config
job = np.run(devices=devices, config=base_config)

for result in job:
    print(f"设备 {result.device_name} 配置结果: {result.ok}")
    if not result.ok:
        print(f"错误: {result.error}")
