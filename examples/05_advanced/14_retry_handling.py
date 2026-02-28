"""
错误处理与重试机制 - 最佳实践
"""
import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import np
from netpulse_sdk.error import NetPulseError

# 场景：执行任务时遇到网络抖动或设备忙，如何优雅地处理错误并重试
devices = ["10.1.1.1", "10.1.1.2"]

def run_task_with_retry(devices, command, max_retries=3):
    """一个简单的带有指数退避重试的执行包装"""
    for attempt in range(max_retries):
        try:
            # 1. 执行任务
            job = np.run(devices=devices, command=command)
            
            # 2. 检查结果
            if job.all_ok:
                return job
            
            # 3. 处理失败
            failed_devices = list(job.failed_commands.keys())
            print(f"尝试 {attempt + 1}: 部分设备提交后任务失败: {failed_devices}")
            
        except NetPulseError as e:
            # SDK 内部会抛出重试标志
            if e.retryable and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"尝试 {attempt + 1}: 遇到可重试异常 {e.type}，等待 {wait_time}s...")
                time.sleep(wait_time)
                continue
            raise e
            
        # 如果是逻辑报错而非连接报错，通常选择不再重试
        if not job.all_ok:
            return job 

# 执行
job = run_task_with_retry(devices, "display version")

if job:
    # 也可以使用 raise_on_error() 快捷抛出异常
    # job.raise_on_error()
    print(f"任务最终状态: {job.status}")
    print(f"成功数: {len(job.succeeded())}")
