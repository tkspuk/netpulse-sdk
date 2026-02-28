"""
任务回调 - 执行完成后自动触发 Webhook
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import paramiko_client as np

job = np.run(
    devices="10.1.1.30",
    command="uptime",
    webhook={
        "url": "https://your-webhook-endpoint.com/api/notify",
        "method": "POST",
        "headers": {"Authorization": "Bearer token123"}
    }
)

print(f"任务已提交，完成后将自动回调 Webhook。Job ID: {job.id}")
