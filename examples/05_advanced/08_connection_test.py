"""
设备连接测试 - 执行前预检设备可达性

新增功能 (P1)
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import np

# === 单设备测试 ===
result = np.test_connection(
    "10.1.1.1", 
    credential={"ref": "secret/net/cisco"} # [可选] 也可以从 Vault 拿密码测连接
)
print(f"设备: {result.host}")
print(f"状态: {'OK' if result.ok else 'FAILED'}")
print(f"延迟: {result.duration_ms}ms" if result.ok else "延迟: N/A")
if result.error:
    print(f"错误: {result.error}")

# # === 批量测试（可选，取消注释运行）===
# devices = ["10.1.1.1", "10.1.1.2"]
# results = np.test_connections(devices)
# for r in results:
#     status = "✓" if r.ok else "✗"
#     print(f"  {status} {r.host}")
