"""
结构化数据查询 - 接口、VLAN、路由
"""
from connection import np
import json

# 接口状态
result = np.collect("10.1.1.1", "show interfaces status").first()
interfaces = json.loads(result.stdout)
print(f"接口数量: {len(interfaces.get('interfaceStatuses', {}))}")

# VLAN 列表
result = np.collect("10.1.1.1", "show vlan").first()
vlans = json.loads(result.stdout)
print(f"VLAN 数量: {len(vlans.get('vlans', {}))}")

# 路由表
result = np.collect("10.1.1.1", "show ip route").first()
routes = json.loads(result.stdout)
print(f"路由条目: {len(routes.get('vrfs', {}).get('default', {}).get('routes', []))}")
