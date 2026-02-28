"""
快捷访问 - [0] / all_ok / outputs
"""
from netpulse_sdk import NetPulseClient

np = NetPulseClient(
    base_url="http://localhost:9000",
    api_key="your-api-key",
    driver="netmiko",
    default_connection_args={"device_type": "cisco_ios", "username": "admin", "password": "password"},
)

# === [0] - 获取第一个结果 ===
result = np.collect("10.1.1.1", "show version")[0]
print(result.stdout)

# === all_ok - 判断是否全部成功 ===
job = np.collect(["10.1.1.1", "10.1.1.2"], "show version")
if job.all_ok:
    print("全部成功！")
else:
    print(f"失败数: {len(job.failed())}")

# === stdout - 获取输出结果 ===
# 1. 如果是单设备任务，job.stdout 直接返回合并后的字符串
single_job = np.collect("10.1.1.1", ["show version", "show ip int br"])
print(f"单设备输出:\n{single_job.stdout}")

# 2. 如果是批量任务，job.stdout 返回 {device: consolidated_stdout} 字典
# 之前例子的 job 是批量设备
for device, output in job.stdout.items():
    print(f"{device}: {len(output)} 字节回显")

# 3. 如果需要精细到每一条命令的输出，使用 stdout_dict
print(f"详细回显字典: {single_job.stdout_dict}")

# === stderr / parsed - 获取错误输出和解析数据 ===
# 同样支持字典映射
stderrs = job.stderr
parsed_data = job.parsed
print(f"解析后的数据: {parsed_data}")
