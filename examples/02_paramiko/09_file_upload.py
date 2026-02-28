"""
文件上传 (File Upload)

演示如何将本地文件直传到目标设备。
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import paramiko_client as np

# 上传：将本地文件直传到目标设备
print("正在上传文件到设备...")
# 寻找本地 connection.py 文件作为上传示例
local_file = os.path.join(os.path.dirname(__file__), "..", "connection.py")

job = np.run(
    devices="10.1.1.30",
    local_upload_file=local_file,
    file_transfer={
        "operation": "upload",
        "remote_path": "/tmp/uploaded_connection.py"
    }
)

result = job.wait()[0]
if result:
    print("上传成功，远程路径: /tmp/uploaded_connection.py")
else:
    print(f"上传失败: {result.stderr}")
