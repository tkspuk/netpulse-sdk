"""
混合厂商 - 每设备指定不同 device_type
"""
from connection import np

# 每设备可覆盖 device_type、username、password
devices = [
    {"host": "10.1.1.1", "device_type": "cisco_ios"},
    {"host": "10.1.1.2", "device_type": "hp_comware"},
    {"host": "10.1.1.3", "device_type": "huawei"},
    {"host": "10.1.1.4", "device_type": "juniper_junos"},
]

for result in np.collect(devices, "display version"):
    print(f"{result.device_name}: {result.ok}")
