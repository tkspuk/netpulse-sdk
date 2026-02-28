"""
批量配置 - Arista 批量操作
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import pyeapi_client as np

arista_switches = ["10.1.1.1", "10.1.1.2", "10.1.1.3"]

# 批量配置 VLAN
config = [
    "vlan 100",
    "name Production",
    "vlan 200",
    "name Development",
]

job = np.run(devices=arista_switches, config=config)
print(f"成功: {len(job.succeeded())}/{len(arista_switches)}")
