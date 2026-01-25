"""
长时间任务 - 提交、监听与状态管理

适用场景：
- 压测任务（stress-ng, iperf 等）
- 批量数据处理
- 任何运行时间较长的任务

演示：
1. 使用 stream() 监听任务（推荐）
2. 手动轮询状态
3. 分离提交和获取
4. 批量任务监控

注意: stream() 不是实时流式输出，而是等待任务完成后一次性返回结果
"""
import time
from connection import np

# ========================================
# 方式 1: 使用 stream() 监听（推荐）
# ========================================

print("=" * 50)
print("方式 1: 使用 stream() 监听长任务")
print("=" * 50)

# 提交一个 10 秒的长任务
job = np.run(
    devices="10.155.30.30",
    command="echo '开始执行...'; for i in 1 2 3 4 5; do echo \"步骤 $i\"; sleep 2; done; echo '执行完成!'",
    ttl=60,
    result_ttl=3600,  # 结果保留 1 小时
)

print(f"任务已提交: {job.id}")
print(f"状态: {job.status}")
print("开始 stream 监听 (会阻塞直到任务完成)...")
print("-" * 50)

start_time = time.time()

# stream() 会自动等待并返回结果
for result in job.stream(poll_interval=1.0):
    elapsed = time.time() - start_time
    print(f"[{elapsed:.1f}s] 收到结果:")
    print(f"  设备: {result.device_name}")
    print(f"  成功: {result.ok}")
    print(f"  输出: {result.output}")

print(f"总耗时: {time.time() - start_time:.1f}s\n")


# ========================================
# 方式 2: 手动轮询状态
# ========================================

print("=" * 50)
print("方式 2: 手动轮询任务状态")
print("=" * 50)

job = np.run(
    devices="10.155.30.30",
    command="sleep 5 && echo 'Task completed!'",
    ttl=300,
)

print(f"任务已提交: {job.id}")

# 定期轮询状态
while not job.is_done():
    job.refresh()  # 从服务端刷新状态
    progress = job.progress()
    print(f"状态: {job.status} | 进度: {progress.completed}/{progress.total}")
    time.sleep(2)

result = job.first()
print(f"任务完成! 状态: {'成功' if result.ok else '失败'}")
print(f"输出: {result.output}\n")


# ========================================
# 方式 3: 分离提交和获取（不同时间点）
# ========================================

print("=" * 50)
print("方式 3: 分离提交和获取")
print("=" * 50)

# 脚本 A: 提交任务并保存 ID
job = np.run(
    devices="10.155.30.30",
    command="uptime",
    ttl=60,
    result_ttl=86400,  # 结果保留 24 小时
)
job_id = job.id
print(f"任务 ID: {job_id}")
print("（可以保存 ID，稍后用另一个脚本查询）")

# 脚本 B: 根据 ID 查询任务
job = np.get_job(job_id)
job.wait()  # 等待完成
print(f"任务状态: {job.status}")
print(f"结果: {job.first().output}\n")


# ========================================
# 方式 4: 批量任务 stream 监控
# ========================================

print("=" * 50)
print("方式 4: 批量任务 stream 监控")
print("=" * 50)

# 同时向多台服务器提交任务
job_group = np.run(
    devices=["10.155.30.30", "10.155.30.31"],
    command="hostname && uptime",
    ttl=60,
)

print(f"批量任务已提交，共 {len(job_group.id)} 个任务")
print("-" * 50)

start_time = time.time()

# JobGroup 的 stream() 会逐个返回已完成设备的结果
for result in job_group.stream(poll_interval=1.0):
    elapsed = time.time() - start_time
    status = "✓" if result.ok else "✗"
    print(f"[{elapsed:.1f}s] {status} {result.device_name}: {result.output[:60]}...")

print("-" * 50)
print(f"总耗时: {time.time() - start_time:.1f}s")
