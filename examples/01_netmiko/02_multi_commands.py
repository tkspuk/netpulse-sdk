"""
多命令执行 - 一次执行多条命令
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import np

commands = [
    "display version",
    "display interface brief",
]

results = np.collect("10.1.1.1", commands)


print(results.stdout)



# for result in results:
#     print(f"命令: {result.command}")
#     print(result.stdout[:200])  # 只显示前200字符
#     print("---")
