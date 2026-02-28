"""
环境变量 - 在执行时注入自定义环境变量
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import paramiko_client as np

job = np.run(
    devices="10.1.1.30",
    command="echo $APP_ENV",
    driver_args={
        "environment": {
            "APP_ENV": "production",
            "DEBUG": "false"
        }
    }
)

print(f"输出: {job.wait()[0].stdout.strip()}")
