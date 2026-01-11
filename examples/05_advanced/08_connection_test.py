"""
设备连接测试 - 执行前预检设备可达性

新增功能 (P1)
"""
from connection import np

# === 单设备测试 ===
result = np.test_connection("10.154.254.1")
print(f"设备: {result.host}")
print(f"成功: {result.success}")
print(f"延迟: {result.latency:.2f}s" if result.latency else "延迟: N/A")
if result.error:
    print(f"错误: {result.error}")

# # === 批量测试（可选，取消注释运行）===
# devices = ["10.154.254.1", "10.154.254.2"]
# results = np.test_connections(devices)
# for r in results:
#     status = "✓" if r.success else "✗"
#     print(f"  {status} {r.host}")
