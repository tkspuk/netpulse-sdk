"""
作业管理 - 查询和取消作业

新增功能 (P2)
"""
from connection import np

# === 查询所有作业 ===
jobs = np.list_jobs()
print(f"总作业数: {len(jobs)}")

# === 按状态过滤 ===
# 状态: queued, started, finished, failed, canceled
finished_jobs = np.list_jobs(status="finished")
print(f"已完成: {len(finished_jobs)}")

failed_jobs = np.list_jobs(status="failed")
print(f"已失败: {len(failed_jobs)}")

# === 按队列过滤 ===
netmiko_jobs = np.list_jobs(queue="netmiko")
print(f"Netmiko 队列: {len(netmiko_jobs)}")

# === 取消单个作业 ===
# cancelled = np.cancel_job("job-id-xxx")
# print(f"取消成功: {cancelled}")

# === 批量取消排队中的作业 ===
# cancelled_ids = np.cancel_jobs(queue="netmiko")
# print(f"已取消: {cancelled_ids}")

# === 查看作业详情 ===
if finished_jobs:
    job = finished_jobs[0]
    print(f"\n作业详情:")
    print(f"  ID: {job.id}")
    print(f"  状态: {job.status}")
