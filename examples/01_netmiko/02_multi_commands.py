"""
多命令执行 - 一次执行多条命令
"""
from connection import np

commands = [
    "display version",
    "display interface brief",
]

for result in np.collect("10.154.254.1", commands):
    print(f"命令: {result.command}")
    print(result.output[:200])  # 只显示前200字符
    print("---")
