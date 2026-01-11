"""
Enums for NetPulse SDK

These enums match the NetPulse API definitions for type safety and IDE autocompletion.
"""

from enum import Enum


class DriverName(str, Enum):
    """Supported driver types for device connections"""

    NETMIKO = "netmiko"
    """SSH connections using Netmiko (Cisco, HP, Huawei, Juniper, etc.)"""

    NAPALM = "napalm"
    """Multi-vendor abstraction layer"""

    PYEAPI = "pyeapi"
    """Arista eAPI connections"""

    PARAMIKO = "paramiko"
    """Linux servers via SSH"""


class QueueStrategy(str, Enum):
    """Queue strategies for job execution"""

    FIFO = "fifo"
    """First-in-first-out: Fair scheduling, new connection each time"""

    PINNED = "pinned"
    """Pinned worker: Connection reuse for frequent operations on same device"""
