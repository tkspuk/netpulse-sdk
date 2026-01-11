"""
Worker 管理 - 查看和管理后台 Worker

新增功能 (P3)
"""
from connection import np

# === 查询所有 Worker ===
workers = np.list_workers()
print(f"总 Worker 数: {len(workers)}")

# === 显示 Worker 详情 ===
for w in workers[:5]:  # 只显示前 5 个
    print(f"  {w['name']}: {w['status']}, 成功任务: {w.get('successful_job_count', 0)}")

# === 按队列过滤 ===
netmiko_workers = np.list_workers(queue="netmiko")
print(f"\nNetmiko Workers: {len(netmiko_workers)}")

# === 统计 Worker 状态 ===
status_count = {}
for w in workers:
    status = w['status']
    status_count[status] = status_count.get(status, 0) + 1

print(f"\n=== Worker 状态统计 ===")
for status, count in status_count.items():
    print(f"  {status}: {count}")

# === 删除 Worker（慎用）===
# deleted = np.delete_workers(name="worker-name")
# print(f"已删除: {deleted}")
