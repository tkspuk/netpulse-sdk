"""
Vault 凭据 - 从 Vault 获取密码
"""
from netpulse_sdk import NetPulseClient

np = NetPulseClient(
    base_url="http://localhost:9000",
    api_key="your-api-key",
    driver="netmiko",
    default_connection_args={
        "device_type": "cisco_ios",
        # 不提供 username/password，由 credential 动态获取
    },
)

result = np.collect(
    devices="10.1.1.1",
    command="show version",
    credential={
        "name": "vault_kv",           # [必需] Provider 名称
        "ref": "secret/network/cisco", # [必需] Vault 路径
        "mount": "kv",                 # [可选] 挂载点
        "field_mapping": {             # [可选] 字段映射
            "username": "user",        # Vault 中 "user" -> connection_args "username"
            "password": "pass",        # Vault 中 "pass" -> connection_args "password"
        },
    },
).first()

print(result.stdout)
