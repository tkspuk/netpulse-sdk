"""
基础查询 - show 命令
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import np

result = np.collect("10.1.1.1", "display version")[0]
print(result.stdout)
