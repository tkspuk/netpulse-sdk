import os
from netpulse_sdk import NetPulseClient

BASE_URL = os.environ.get("NETPULSE_URL", "http://localhost:9000")
API_KEY = os.environ.get("NETPULSE_API_KEY", "your-api-key-here")

# ---- Netmiko Client (Switches/Routers) ----
netmiko_client = NetPulseClient(
    base_url=BASE_URL,
    api_key=API_KEY,
    driver="netmiko",
    default_connection_args={
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "password",
    },
)

# ---- Paramiko Client (Linux Servers) ----
paramiko_client = NetPulseClient(
    base_url=BASE_URL,
    api_key=API_KEY,
    driver="paramiko",
    default_connection_args={
        "username": "admin",
        "password": "password",
    },
)

# ---- PyEAPI Client (Arista EOS) ----
pyeapi_client = NetPulseClient(
    base_url=BASE_URL,
    api_key=API_KEY,
    driver="pyeapi",
    default_connection_args={
        "username": "admin",
        "password": "password",
    },
)

def get_client(driver_name: str = "netmiko") -> NetPulseClient:
    """Returns the pre-configured NetPulseClient for the specified driver."""
    clients = {
        "netmiko": netmiko_client,
        "paramiko": paramiko_client,
        "pyeapi": pyeapi_client,
    }
    return clients.get(driver_name, netmiko_client)

# Default alias for simple scripts
np = netmiko_client
