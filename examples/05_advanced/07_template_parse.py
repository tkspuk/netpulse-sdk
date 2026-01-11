"""
输出解析模板 - 结构化命令输出

演示使用 TextFSM/TTP 等模板解析器将命令输出转换为结构化数据

注意：
- 解析在 NetPulse 服务端执行，模板文件需要服务端能访问
- 常见解析器: textfsm, ttp, genie
- 可使用 ntc-templates 社区模板库
"""
from netpulse_sdk import NetPulseClient

np = NetPulseClient(
    base_url="http://localhost:9000",
    api_key="your-api-key",
    driver="netmiko",
    default_connection_args={"device_type": "cisco_ios", "username": "admin", "password": "password"},
)

# ========================================
# 场景 1: 使用外部 TextFSM 模板
# ========================================
# 假设模板文件 /etc/netpulse/templates/show_ip_int_brief.textfsm:
# ```
# Value INTERFACE (\S+)
# Value IPADDR (\S+)
# Value STATUS (up|down|administratively down)
# Value PROTO (up|down)
#
# Start
#   ^${INTERFACE}\s+${IPADDR}\s+\S+\s+\S+\s+${STATUS}\s+${PROTO} -> Record
# ```

result = np.run(
    devices="10.1.1.1",
    command="show ip interface brief",
    parsing={
        "name": "textfsm",
        "template": "file:///etc/netpulse/templates/show_ip_int_brief.textfsm",
    },
).first()

if result.ok:
    # 解析后的输出是结构化数据（列表或字典）
    print("接口状态:")
    for intf in result.output:
        print(f"  {intf['INTERFACE']}: {intf['IPADDR']} ({intf['STATUS']})")


# ========================================
# 场景 2: 使用 ntc-templates 社区模板
# ========================================
# ntc-templates 是预定义的 TextFSM 模板库
# 模板名通常按 "platform_command" 格式命名

result = np.run(
    devices="10.1.1.1",
    command="show version",
    parsing={
        "name": "ntc-templates",  # 使用 ntc-templates 解析器
        "template": "cisco_ios_show_version",  # 社区模板名
    },
).first()

if result.ok:
    version_info = result.output[0] if result.output else {}
    print(f"设备型号: {version_info.get('hardware', 'N/A')}")
    print(f"软件版本: {version_info.get('version', 'N/A')}")
    print(f"运行时间: {version_info.get('uptime', 'N/A')}")


# ========================================
# 场景 3: 批量采集 + 解析
# ========================================
# 从多台设备采集并解析 BGP 邻居信息

devices = ["10.1.1.1", "10.1.1.2", "10.1.1.3"]

job_group = np.run(
    devices=devices,
    command="show ip bgp summary",
    parsing={
        "name": "textfsm",
        "template": "file:///etc/netpulse/templates/show_ip_bgp_summary.textfsm",
    },
)

print("\nBGP 邻居汇总:")
for result in job_group.wait_all():
    if result.ok and result.output:
        print(f"\n{result.device}:")
        for neighbor in result.output:
            print(f"  邻居 {neighbor.get('neighbor_ip')}: "
                  f"AS {neighbor.get('remote_as')}, "
                  f"前缀数 {neighbor.get('prefixes_received')}")
    else:
        print(f"\n{result.device}: 采集失败")
