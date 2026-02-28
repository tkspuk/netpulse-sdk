"""
JSON 格式输出 - Arista 结构化数据
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import pyeapi_client as np
import json

# PyEAPI 返回 JSON 格式的结构化数据
result = np.collect("10.1.1.1", "show version")[0]

# 解析 JSON 输出
data = json.loads(result.stdout)
print(f"型号: {data.get('modelName')}")
print(f"版本: {data.get('version')}")
