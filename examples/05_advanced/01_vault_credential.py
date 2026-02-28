import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from connection import np

# 不提供 connection_args，由 credential 动态从 Vault 获取身份信息
job = np.collect(
    devices="10.1.1.1",
    command="show version",
    credential={
        "ref": "secret/network/cisco",
        "field_mapping": {
            "username": "user",
            "password": "pass",
        },
    },
)

print(job[0].stdout)
