"""
SSH 密钥认证 - 使用私钥登录
"""
from netpulse_sdk import NetPulseClient

np = NetPulseClient(
    base_url="http://localhost:9000",
    api_key="your-api-key",
    driver="paramiko",
    default_connection_args={
        "username": "root",
        "pkey_string": open("/root/.ssh/id_rsa").read(),  # 私钥内容
        # 或使用环境变量: "pkey_string": os.environ.get("SSH_PRIVATE_KEY"),
    },
)

result = np.collect("10.1.1.1", "whoami").first()
print(result.stdout)
