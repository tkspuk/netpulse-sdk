"""
输出自动解析 - 获取结构化 JSON 数据
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import paramiko_client as np

# 执行命令并指定 TextFSM 模板进行解析
job = np.collect(
    "10.1.1.30", 
    "df -h",
    parsing={
        "name": "textfsm",
        "template": "linux_df.textfsm"  # 假设服务端已配置此模板
    }
)

result = job.wait()[0]
if result.ok:
    print("解析后的磁盘数据:")
    for drive in result.parsed:
        print(f"挂载点: {drive['MOUNT_POINT']}, 使用率: {drive['PERCENT_USED']}")
