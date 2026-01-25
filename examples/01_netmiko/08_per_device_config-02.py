"""
每设备不同配置 - config 覆盖
"""
from connection import np

# 设备可带 config 字段覆盖 base 配置
devices = [
    "10.210.253.18",
    "10.210.253.19",
    "10.210.253.20",
    "10.210.253.21",
    "10.210.253.34",
    "10.210.253.35",
    "10.210.253.36",
    "10.210.253.37",
]

base_config = [
    "interface range FourHundredGigE 1/0/95 to FourHundredGigE 1/0/128",
    "port link-mode bridge",
    "port link-type trunk",
    "undo port trunk permit vlan 1",
    "port trunk permit vlan 51",
    "port trunk pvid vlan 51",
    "link-delay down 0",
    "link-delay up 2",
    "priority-flow-control enable",
    "priority-flow-control no-drop dot1p 5",
    "priority-flow-control dot1p 5 headroom 2000",
    "priority-flow-control dot1p 5 ingress-buffer dynamic 6",
    "priority-flow-control deadlock enable",
    "qos trust dscp",
    "qos wfq byte-count",
    "qos wfq ef group 1 byte-count 96",
    "qos wfq cs6 group sp",
    "qos wfq cs7 group sp",
    "qos wred queue 5 drop-level 0 low-limit 6000 high-limit 12000 discard-probability 40",
    "qos wred queue 5 drop-level 1 low-limit 6000 high-limit 12000 discard-probability 40",
    "qos wred queue 5 drop-level 2 low-limit 6000 high-limit 12000 discard-probability 40",
    "qos wred queue 5 ecn",
    "qos wred queue 5 weighting-constant 0",
]

# 混合模式：有的设备用 base_config，有的用自己的 config
job = np.run(devices=devices, config=base_config,)

for result in job:
    print(f"设备 {result.device_name} 配置结果: {result.ok}")
    if not result.ok:
        print(f"错误: {result.error}")
