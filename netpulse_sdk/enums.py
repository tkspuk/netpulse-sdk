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


class JobStatus(str, Enum):
    """Possible statuses of a NetPulse job"""

    QUEUED = "queued"
    """Job is waiting in the queue"""

    STARTED = "started"
    """Job is being executed by a worker"""

    FINISHED = "finished"
    """Job completed successfully"""

    FAILED = "failed"
    """Job execution failed"""

    DEFERRED = "deferred"
    """Job execution is deferred"""

    CANCELED = "canceled"
    """Job was canceled by the user"""


class TaskStatus(str, Enum):
    """Possible statuses of a detached task"""

    LAUNCHING = "launching"
    """Task is being initialized on the remote host"""

    RUNNING = "running"
    """Task is currently executing on the remote host"""

    COMPLETED = "completed"
    """Task has finished execution"""
