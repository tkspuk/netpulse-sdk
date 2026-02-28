"""
脚本执行 - 直接执行多行 Python/Bash 脚本
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import paramiko_client as np

# 演示直接执行一段 Python 脚本，而不需要先上传文件
python_script = """
import os
import sys
print(f"Platform: {sys.platform}")
print(f"User: {os.getlogin()}")
"""

job = np.run(
    devices="10.1.1.30",
    driver_args={
        "script_content": python_script,
        "script_interpreter": "python3"  # 指定解释器，默认为 bash
    }
)

print(f"脚本输出:\n{job.wait()[0].stdout}")
