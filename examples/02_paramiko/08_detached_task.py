"""
后台脱机任务 (Detached Tasks)

适用于希望关闭连接后任务依然在远端执行的场景（仅 Paramiko 支持）。
"""
import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import paramiko_client as np

# 1. 提交后台脱机任务
print("提交后台任务...")
job = np.run(
    devices="10.1.1.30",
    command="sleep 60 && echo 'Done'",
    detach=True
)

task_id = job.task_id
print(f"作业 ID: {job.id}")
print(f"后台任务 ID: {task_id}")

# 2. 查询实时日志
print("\n获取实时日志...")
time.sleep(2)
task_data = np.get_detached_task(task_id)
print(f"状态: {task_data.get('status')}")
print(f"当前输出: {task_data.get('stdout', '')}")

# 3. 强杀任务
print(f"\n中止任务 {task_id}...")
if np.cancel_detached_task(task_id):
    print("中止成功")
else:
    print("中止失败或任务已结束")
