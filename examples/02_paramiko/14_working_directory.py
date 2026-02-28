"""
工作目录 - 在特定路径下执行命令
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import paramiko_client as np

job = np.run(
    devices="10.1.1.30",
    command="ls",
    driver_args={
        "working_directory": "/var/log"  # 相当于先 cd /var/log 再执行
    }
)

print(f"日志目录内容:\n{job.wait()[0].stdout}")
