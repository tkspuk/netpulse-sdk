"""
文件下载 (File Download)

演示如何从设备拉取文件并保存到本地。
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import paramiko_client as np

# 下载：从设备拉取文件并保存到本地
print("正在从设备下载文件...")
job = np.run(
    devices="10.1.1.30",
    file_transfer={
        "operation": "download",
        "remote_path": "/etc/hostname"
    }
)

result = job.wait()[0]
if result.ok and result.download_url:
    local_path = os.path.join(os.path.dirname(__file__), "fetched_hostname")
    np.fetch_staged_file(result.download_url, local_path)
    print(f"下载成功，保存至: {local_path}")
else:
    print(f"下载失败: {result.stderr}")
