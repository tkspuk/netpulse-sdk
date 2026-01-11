"""
模板渲染 - Jinja2 动态生成配置

演示三种场景：
1. 内联模板 - 模板字符串直接写在代码中
2. 外部模板文件 - 从文件系统加载模板
3. 批量设备模板 - 同一模板应用于多个设备
"""
from netpulse_sdk import NetPulseClient

np = NetPulseClient(
    base_url="http://localhost:9000",
    api_key="your-api-key",
    driver="netmiko",
    default_connection_args={"device_type": "cisco_ios", "username": "admin", "password": "password"},
)

# ========================================
# 场景 1: 内联模板（plain）
# ========================================
# 适用于简单的一次性模板

result = np.run(
    devices="10.1.1.1",
    config="interface {{ interface }}\n description {{ desc }}",
    rendering={
        "name": "jinja2",
        "template": "plain",  # plain 表示直接使用 config 字段作为模板
        "context": {
            "interface": "GigabitEthernet0/1",
            "desc": "WAN-Link",
        },
    },
).first()

print(f"内联模板配置: {result.ok}")

# ========================================
# 场景 2: 外部模板文件
# ========================================
# 适用于复杂的、可复用的配置模板
# 模板文件需要 NetPulse 服务端能访问

# 假设模板文件 /etc/netpulse/templates/interface_config.j2 内容如下：
# ```
# interface {{ interface }}
#   description {{ description }}
#   ip address {{ ip_address }} {{ subnet_mask }}
#   no shutdown
# ```

result = np.run(
    devices="10.1.1.1",
    config="",  # 配置将由模板渲染生成，此处留空或填占位符
    rendering={
        "name": "jinja2",
        "template": "file:///etc/netpulse/templates/interface_config.j2",
        "context": {
            "interface": "GigabitEthernet0/1",
            "description": "WAN-Link-Primary",
            "ip_address": "192.168.1.1",
            "subnet_mask": "255.255.255.0",
        },
    },
).first()

print(f"外部模板配置: {result.ok}")

# ========================================
# 场景 3: 批量设备 + 模板
# ========================================
# 同一模板应用于多个设备，每个设备使用相同变量

devices = ["10.1.1.1", "10.1.1.2", "10.1.1.3"]

job_group = np.run(
    devices=devices,
    config="ntp server {{ ntp_server }}\nlogging host {{ syslog_server }}",
    rendering={
        "name": "jinja2",
        "template": "plain",
        "context": {
            "ntp_server": "10.0.0.1",
            "syslog_server": "10.0.0.2",
        },
    },
)

# 等待所有设备完成
for result in job_group.wait_all():
    print(f"{result.device}: 配置{'成功' if result.ok else '失败'}")
