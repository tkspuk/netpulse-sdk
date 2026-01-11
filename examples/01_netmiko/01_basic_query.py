"""
基础查询 - show 命令
"""
from connection import np

result = np.collect("10.154.254.1", "display version").first()
print(result.output)  # 推荐用 output
