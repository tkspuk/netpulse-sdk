"""
结构化数据查询 - 接口、VLAN、路由
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import pyeapi_client as np
import json

# 接口状态
job = np.collect("10.1.1.1", "show interfaces status")
interfaces = json.loads(job.stdout)
print(f"接口数量: {len(interfaces.get('interfaceStatuses', {}))}")

# VLAN 列表
job = np.collect("10.1.1.1", "show vlan")
vlans = json.loads(job.stdout)
print(f"VLAN 数量: {len(vlans.get('vlans', {}))}")

# 路由表
job = np.collect("10.1.1.1", "show ip route")
routes = json.loads(job.stdout)
print(f"路由条目: {len(routes.get('vrfs', {}).get('default', {}).get('routes', []))}")
