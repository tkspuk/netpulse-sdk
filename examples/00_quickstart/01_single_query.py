"""
单设备查询 - 展示多种写法
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import np

# === 写法1: for 循环迭代（通用） ===
for result in np.collect("10.1.1.1", "display version"):
    print(result.stdout)   # 成功显示标准输出
    print(result.job_id)   # 获取 Job ID

# === 写法2: 直接读 stdout（单设备推荐） ===
job = np.collect("10.1.1.1", "display version")
print(job.stdout)

# === 写法3: 索引访问单个 Result ===
# result = np.collect("10.1.1.1", "display version")[0]
# print(result.stdout)
