"""
单设备查询 - 展示多种写法
"""
from connection import np

# === 写法1: for 循环迭代（通用） ===
for result in np.collect("10.154.254.1", "display version"):
    print(result.output)   # 成功显示输出，失败显示错误
    print(result.job_id)   # 获取 Job ID

# # === 写法2: first() 快捷方式（单设备推荐） ===
# result = np.collect("10.154.254.1", "display version").first()
# print(result.output)
