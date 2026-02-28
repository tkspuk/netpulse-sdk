"""
Sudo 执行 - 以超级用户权限运行命令
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import paramiko_client as np

# 使用 driver_args 中的 sudo 参数
job = np.run(
    devices="10.1.1.30",
    command="apt-get update",  # 需要 sudo 的命令
    driver_args={
        "sudo": True,
        "sudo_password": "your-sudo-password"  # 如果需要密码
    }
)

result = job.wait()[0]
print(f"执行成功: {result.ok}")
print(f"输出内容:\n{result.stdout}")
