"""
NetPulse client
"""

import logging
from typing import List, Literal, Optional, Union

from .error import NetPulseError
from .job import Job, JobGroup
from .transport import HTTPClient

log = logging.getLogger(__name__)


class NetPulseClient:
    """NetPulse SDK client"""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 30,
        driver: str = "netmiko",
        default_connection_args: Optional[dict] = None,
        pool_connections: int = 10,
        pool_maxsize: int = 200,
        max_retries: int = 3,
    ):
        """Initialize NetPulse client

        Args:
            base_url: NetPulse API URL, e.g., http://localhost:9000
            api_key: API key
            timeout: HTTP request timeout in seconds
            driver: Default driver (netmiko, napalm, pyeapi, paramiko)
            default_connection_args: Default connection arguments (username, password, etc.)
            pool_connections: HTTP connection pool count (default 10)
            pool_maxsize: Maximum connections per pool (default 200, increase to 500 for large batches)
            max_retries: HTTP request auto-retry count (default 3)
        """
        self._http = HTTPClient(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=max_retries,
        )
        self.driver = driver
        self.default_connection_args = default_connection_args or {}

    def run(
        self,
        devices: Union[List[str], str, List[dict]],
        commands: Union[List[str], str] = None,
        config: Union[List[str], str] = None,
        mode: Literal["auto", "exec", "bulk"] = "auto",
        timeout: int = 300,
        connection_args: Optional[dict] = None,
        driver: Optional[str] = None,
        driver_args: Optional[dict] = None,
        credential: Optional[dict] = None,
        rendering: Optional[dict] = None,
        parsing: Optional[dict] = None,
        queue_strategy: Optional[Literal["fifo", "pinned"]] = None,
        result_ttl: Optional[int] = None,
        webhook: Optional[dict] = None,
    ) -> Job:
        """Execute commands or configuration

        Args:
            devices: Device list or single device (IP/hostname or connection_args dict)
            commands: Command list or single command (query commands, mutually exclusive with config)
            config: Configuration command list or single command (mutually exclusive with commands)
            mode: Execution mode (auto, exec for single device, bulk for multiple devices)
            timeout: Job timeout in seconds (ttl parameter)
            connection_args: Connection arguments (overrides default_connection_args)
            driver: Driver name (overrides default driver)
            driver_args: Driver-specific parameters (read_timeout, delay_factor, etc.)
            credential: Vault credential reference (name, ref, mount, field_mapping, etc.)
            rendering: Template rendering configuration (name, template, context)
            parsing: Output parsing configuration (name, template, context)
            queue_strategy: Queue strategy (fifo or pinned)
            result_ttl: Result retention time in seconds
            webhook: Webhook callback configuration (url, method, headers, etc.)

        Returns:
            Job or JobGroup instance
        """
        devices = [devices] if isinstance(devices, str) else devices

        if commands and config:
            raise ValueError("commands and config are mutually exclusive")
        if not commands and not config:
            raise ValueError("Either commands or config must be specified")

        operation = commands if commands else config
        operation = [operation] if isinstance(operation, str) else operation
        operation_type = "command" if commands else "config"

        if not devices:
            raise ValueError("devices cannot be empty")

        conn_args = {**self.default_connection_args}
        if connection_args:
            conn_args.update(connection_args)

        api_mode = self._select_api(devices, mode)
        use_driver = driver or self.driver

        if api_mode == "exec":
            device = devices[0] if isinstance(devices[0], str) else devices[0].get("host")
            return self._call_exec_api(
                device=device,
                operation=operation,
                operation_type=operation_type,
                timeout=timeout,
                connection_args=conn_args,
                driver=use_driver,
                driver_args=driver_args,
                credential=credential,
                rendering=rendering,
                parsing=parsing,
                queue_strategy=queue_strategy,
                result_ttl=result_ttl,
                webhook=webhook,
            )
        else:
            return self._call_bulk_api(
                devices=devices,
                operation=operation,
                operation_type=operation_type,
                timeout=timeout,
                connection_args=conn_args,
                driver=use_driver,
                driver_args=driver_args,
                credential=credential,
                rendering=rendering,
                parsing=parsing,
                queue_strategy=queue_strategy,
                result_ttl=result_ttl,
                webhook=webhook,
            )

    def collect(
        self,
        devices: Union[List[str], str, List[dict]],
        commands: Union[List[str], str],
        timeout: int = 300,
        connection_args: Optional[dict] = None,
        driver: Optional[str] = None,
        driver_args: Optional[dict] = None,
        credential: Optional[dict] = None,
        parsing: Optional[dict] = None,
        queue_strategy: Optional[Literal["fifo", "pinned"]] = None,
        result_ttl: Optional[int] = None,
        webhook: Optional[dict] = None,
    ) -> Job:
        """Read-only collection (semantic wrapper)

        Equivalent to run(), but explicitly marked as read-only operation

        Args:
            devices: Device list or single device
            commands: Command list or single command
            timeout: Job timeout in seconds
            connection_args: Connection arguments
            driver: Driver name
            driver_args: Driver-specific parameters
            credential: Vault credential reference
            parsing: Output parsing configuration
            queue_strategy: Queue strategy
            result_ttl: Result retention time
            webhook: Webhook callback configuration
        """
        return self.run(
            devices=devices,
            commands=commands,
            mode="auto",
            timeout=timeout,
            connection_args=connection_args,
            driver=driver,
            driver_args=driver_args,
            credential=credential,
            parsing=parsing,
            queue_strategy=queue_strategy,
            result_ttl=result_ttl,
            webhook=webhook,
        )

    def get_job(self, job_id: str) -> Job:
        """Get Job by ID

        Args:
            job_id: Job ID

        Returns:
            Job instance
        """
        resp = self._http.get("/job", params={"id": job_id})
        if not resp["data"] or len(resp["data"]) == 0:
            raise NetPulseError(f"Job {job_id} not found")

        job_data = resp["data"][0]
        return Job(client=self, job_data=job_data, device_name="unknown", commands=[])

    def _select_api(
        self, devices: List[str], mode: Literal["auto", "exec", "bulk"]
    ) -> Literal["exec", "bulk"]:
        """Select exec or bulk API

        Strategy:
        - mode=exec: Single device only, raises error if multiple
        - mode=bulk: Use bulk API
        - mode=auto: exec for single device, bulk for multiple devices
        """
        if mode == "exec":
            if len(devices) != 1:
                raise ValueError("exec mode only supports single device")
            return "exec"

        if mode == "bulk":
            return "bulk"

        if len(devices) == 1:
            return "exec"
        else:
            return "bulk"

    def _call_exec_api(
        self,
        device: str,
        operation: List[str],
        operation_type: str,
        timeout: int,
        connection_args: dict,
        driver: str,
        driver_args: Optional[dict] = None,
        credential: Optional[dict] = None,
        rendering: Optional[dict] = None,
        parsing: Optional[dict] = None,
        queue_strategy: Optional[str] = None,
        result_ttl: Optional[int] = None,
        webhook: Optional[dict] = None,
    ) -> Job:
        """Call POST /device/exec

        Returns single Job
        """
        payload = {
            "driver": driver,
            "connection_args": {
                **connection_args,
                "host": device,
            },
            operation_type: operation,
            "ttl": timeout,
        }
        if driver_args:
            payload["driver_args"] = driver_args
        if credential:
            payload["credential"] = credential
        if rendering:
            payload["rendering"] = rendering
        if parsing:
            payload["parsing"] = parsing
        if queue_strategy:
            payload["queue_strategy"] = queue_strategy
        if result_ttl:
            payload["result_ttl"] = result_ttl
        if webhook:
            payload["webhook"] = webhook

        resp = self._http.post("/device/exec", json=payload)
        job_data = resp["data"]

        return Job(client=self, job_data=job_data, device_name=device, commands=operation)

    def _call_bulk_api(
        self,
        devices: List[Union[str, dict]],
        operation: List[str],
        operation_type: str,
        timeout: int,
        connection_args: dict,
        driver: str,
        driver_args: Optional[dict] = None,
        credential: Optional[dict] = None,
        rendering: Optional[dict] = None,
        parsing: Optional[dict] = None,
        queue_strategy: Optional[str] = None,
        result_ttl: Optional[int] = None,
        webhook: Optional[dict] = None,
    ) -> Job:
        """Call POST /device/bulk

        Returns JobGroup (manages multiple Jobs)
        """
        normalized_devices = []
        for device in devices:
            if isinstance(device, str):
                normalized_devices.append({"host": device})
            elif isinstance(device, dict):
                normalized_devices.append(device)
            else:
                raise ValueError(f"Unsupported device type: {type(device)}")

        payload = {
            "driver": driver,
            "connection_args": connection_args,
            "devices": normalized_devices,
            operation_type: operation,
            "ttl": timeout,
        }
        if driver_args:
            payload["driver_args"] = driver_args
        if credential:
            payload["credential"] = credential
        if rendering:
            payload["rendering"] = rendering
        if parsing:
            payload["parsing"] = parsing
        if queue_strategy:
            payload["queue_strategy"] = queue_strategy
        if result_ttl:
            payload["result_ttl"] = result_ttl
        if webhook:
            payload["webhook"] = webhook

        resp = self._http.post("/device/bulk", json=payload)

        data = resp["data"]
        if not data:
            raise NetPulseError("Bulk API returned empty data")

        succeeded = data.get("succeeded", [])
        failed = data.get("failed", [])

        if failed:
            log.debug(f"Bulk API response - succeeded: {len(succeeded)}, failed: {failed}")
            if succeeded:
                log.debug(
                    f"First succeeded job structure: {list(succeeded[0].keys()) if isinstance(succeeded[0], dict) else 'not a dict'}"
                )

        if failed:
            log.warning(f"Some devices failed to submit: {failed}")

        if not succeeded:
            raise NetPulseError(f"All devices failed to submit: {failed}")

        jobs = []
        used_indices = set()

        for job_data in succeeded:
            device_name = None

            if isinstance(job_data, dict):
                conn_args = job_data.get("connection_args", {})
                if isinstance(conn_args, dict):
                    device_name = conn_args.get("host")

                if not device_name:
                    device_name = job_data.get("device") or job_data.get("host")

            if not device_name:
                for idx, d in enumerate(devices):
                    if idx not in used_indices:
                        if isinstance(d, str):
                            device_name = d
                        elif isinstance(d, dict):
                            device_name = d.get("host") or d.get("device")
                        if device_name:
                            used_indices.add(idx)
                            break
                if not device_name and len(jobs) < len(devices):
                    idx = len(jobs)
                    if idx < len(devices):
                        d = devices[idx]
                        if isinstance(d, str):
                            device_name = d
                        elif isinstance(d, dict):
                            device_name = d.get("host") or d.get("device")
                        used_indices.add(idx)

            if not device_name:
                device_name = "unknown"

            jobs.append(
                Job(client=self, job_data=job_data, device_name=device_name, commands=operation)
            )

        return JobGroup(jobs=jobs, failed_devices=failed)

    def close(self):
        """Close client"""
        self._http.close()

    def __enter__(self):
        """Support with statement"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support with statement"""
        self.close()
