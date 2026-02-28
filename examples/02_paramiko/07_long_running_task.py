"""
长耗时任务 - 提交与进度监听

演示如何使用 wait() 和回调函数监听任务进度。
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import paramiko_client as np

# 1. 提交长耗时任务 (例如执行 5 秒的循环)
print("正在提交长任务...")
job = np.run(
    devices="10.1.1.30",
    command="for i in {1..5}; do echo \"Step $i\"; sleep 1; done",
    ttl=60
)

# 2. 定义进度回调函数
def progress_callback(progress):
    # progress 是 JobProgress 对象
    print(f"进度更新: [{progress.completed}/{progress.total}] 状态: 运行中...")

# 3. 等待任务完成并查看进度
print(f"开始轮询 (Job ID: {job.id})...")
job.wait(poll_interval=1.0, callback=progress_callback)

# 4. 获取结果
result = job[0]
print("\n任务完成!")
print(f"标准输出:\n{result.stdout}")
