"""
交互式自动应答 - 处理 [Y/n] 等提示
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import paramiko_client as np

# 使用 expect_map 定义：碰到什么字符，就自动回车发送什么内容
job = np.run(
    devices="10.1.1.30",
    command="rm -i test_file.txt",  # 会触发确认提示
    driver_args={
        "expect_map": {
            "remove regular empty file": "y"  # 匹配到提示语，自动发送 y
        }
    }
)

result = job.wait()[0]
print(f"输出:\n{result.stdout}")
