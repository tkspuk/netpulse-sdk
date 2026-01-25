"""
使用模板渲染配置 - 从模板生成配置命令
"""
from connection import np

# 设备列表
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

# 配置模板（Jinja2 格式）
config_template = """interface range FourHundredGigE 1/0/{{ start_port }} to FourHundredGigE 1/0/{{ end_port }}
port link-mode bridge
port link-type trunk
undo port trunk permit vlan 1
port trunk permit vlan {{ vlan_id }}
port trunk pvid vlan {{ vlan_id }}
link-delay down 0
link-delay up 2
priority-flow-control enable
priority-flow-control no-drop dot1p 5
priority-flow-control dot1p 5 headroom 2000
priority-flow-control dot1p 5 ingress-buffer dynamic 6
priority-flow-control deadlock enable
qos trust dscp
qos wfq byte-count
qos wfq ef group 1 byte-count 96
qos wfq cs6 group sp
qos wfq cs7 group sp
qos wred queue 5 drop-level 0 low-limit 6000 high-limit 12000 discard-probability 40
qos wred queue 5 drop-level 1 low-limit 6000 high-limit 12000 discard-probability 40
qos wred queue 5 drop-level 2 low-limit 6000 high-limit 12000 discard-probability 40
qos wred queue 5 ecn
qos wred queue 5 weighting-constant 0"""

# 模板变量
template_vars = {
    "start_port": 95,
    "end_port": 128,
    "vlan_id": 51,
}

# 使用模板执行配置
# 注意：当使用 rendering 时，config 必须是空字典 {}
# API 会用渲染后的模板结果替换它
job = np.run(
    devices=devices,
    config={},  # 使用模板时，config 必须是空字典
    rendering={
        "name": "jinja2",  # 渲染器名称（必需）
        "template": config_template,  # 模板内容
        "context": template_vars,  # 变量
    },
)

for result in job:
    print(f"设备 {result.device_name} 配置结果: {result.ok}")
    if not result.ok:
        print(f"错误: {result.error}")


