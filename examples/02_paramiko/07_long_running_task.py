"""
长时间任务 - 异步提交和状态轮询

适用场景：
- 压测任务（stress-ng, iperf 等）
- 批量数据处理
- 任何运行时间较长的任务

演示：
1. 提交任务（不阻塞）
2. 定期轮询状态
3. 分离提交和获取（不同脚本/时间点）
"""
import time
from connection import np

# ========================================
# 场景 1: 提交任务并轮询状态
# ========================================

# 提交长时间任务（不阻塞）
job = np.run(
    devices="10.155.30.35",
    command="sleep 10 && echo 'Task completed!'",  # 模拟长时间任务
    ttl=300,           # 任务超时 5 分钟
    result_ttl=3600,   # 结果保留 1 小时
)

print(f"任务已提交: {job.id}")
print(f"初始状态: {job.status}")

# 定期轮询状态
while not job.is_done():
    job.refresh()  # 从服务端刷新状态
    progress = job.progress()
    print(f"状态: {job.status} | 进度: {progress.completed}/{progress.total}")
    time.sleep(2)  # 每 2 秒检查一次

# 获取最终结果
result = job.first()
print(f"\n任务完成!")
print(f"状态: {'成功' if result.ok else '失败'}")
print(f"输出: {result.output}")


# ========================================
# 场景 2: 分离提交和获取（不同时间点）
# ========================================

# 脚本 A: 提交任务并保存 ID
job = np.run(
    devices="10.155.30.35",
    command="long_running_task.sh",
    ttl=3600,        # 1 小时超时
    result_ttl=86400,  # 结果保留 24 小时
)
job_id = job.id
print(f"请保存任务 ID: {job_id}")

# ... 可以关闭脚本，稍后再执行下面的代码 ...

# 脚本 B: 根据 ID 查询任务
job = np.get_job(job_id)
print(f"任务状态: {job.status}")

if job.is_done():
    result = job.first()
    print(f"结果: {result.output}")
else:
    print(f"任务仍在运行...")


# ========================================
# 场景 3: 批量任务状态监控
# ========================================

# 同时向多台服务器提交任务
job_group = np.run(
    devices=["10.155.30.35", "10.155.30.36", "10.155.30.37"],
    command="stress-ng --cpu 2 --timeout 30s",
    ttl=120,
)

print(f"\n批量任务已提交，共 {len(job_group.id)} 个任务")

# 监控整体进度
while not job_group.is_done():
    job_group.refresh()
    progress = job_group.progress()
    print(f"总体进度: {progress.completed}/{progress.total} "
          f"(失败: {progress.failed}, 运行中: {progress.running})")
    time.sleep(3)

# 汇总结果
print("\n===== 任务完成 =====")
for result in job_group.results():
    status = "✓" if result.ok else "✗"
    print(f"{status} {result.device_name}: {result.output[:50]}...")
