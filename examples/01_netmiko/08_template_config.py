"""
使用模板渲染配置 - 从模板生成配置命令

演示：如何使用 Jinja2 模板动态生成设备配置（如 Banner, Interface）
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import np

# 设备列表
devices = ["10.1.1.1", "10.1.1.2"]

# 配置模板（Jinja2 格式）
# 演示配置登录 Banner
banner_template = """
header login %
***************************************************
* Welcome to NetPulse-Managed Device: {{ hostname }}
* Site: {{ site_name }}
* Admin: {{ admin_user }}
***************************************************
%
"""

# 使用模板执行配置
# 注意：当使用 rendering 渲染引擎时，config 字段可以留空字符串或 {}
job = np.run(
    devices=devices,
    config={},
    rendering={
        "name": "jinja2",             # 渲染器名称
        "template": banner_template,     # 模板串
        "context": {                   # 注入模板的变量
            "site_name": "DataCenter-01",
            "admin_user": "net-ops",
        },
    },
)

for result in job:
    # 提示：hostname 变量在模板中如果没有显式传入，
    # 某些驱动可能会尝试从元数据中获取，但通常推荐在 context 中显式定义或使用 rendering 的高级模式。
    print(f"设备 {result.device_name} Banner 配置结果: {result.ok}")
