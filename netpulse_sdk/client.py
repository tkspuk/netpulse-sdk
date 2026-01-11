"""
NetPulse client
"""

import logging
import os
from typing import List, Literal, Optional, Union

from .error import NetPulseError
from .job import Job, JobGroup
from .result import ConnectionTestResult
from .transport import HTTPClient

log = logging.getLogger(__name__)


class NetPulseClient:
    """NetPulse SDK client"""

    DEFAULT_DRIVER_ARGS = {
        "read_timeout": 60,
        "delay_factor": 3,
        "max_loops": 5000,
    }

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
        driver: str = "netmiko",
        default_connection_args: Optional[dict] = None,
        pool_connections: int = 10,
        pool_maxsize: int = 200,
        max_retries: int = 3,
        profile: Optional[str] = None,
        config_path: Optional[str] = None,
    ):
        """Initialize NetPulse client

        Args:
            base_url: NetPulse API URL. Falls back to config file, then NETPULSE_URL env var.
            api_key: API key. Falls back to config file, then NETPULSE_API_KEY env var.
            timeout: HTTP request timeout in seconds
            driver: Default driver (netmiko, napalm, pyeapi, paramiko)
            default_connection_args: Default connection arguments (username, password, etc.)
            pool_connections: HTTP connection pool count (default 10)
            pool_maxsize: Maximum connections per pool (default 200, increase to 500 for large batches)
            max_retries: HTTP request auto-retry count (default 3)
            profile: Config profile name (default uses 'default' profile)
            config_path: Explicit config file path (optional)
        """
        # Load config file
        from .config import load_config, get_config_value

        config = load_config(config_path=config_path, profile=profile)

        # Priority: explicit param > config file > environment variable
        base_url = (
            base_url or get_config_value(config, "base_url") or os.environ.get("NETPULSE_URL")
        )
        api_key = (
            api_key or get_config_value(config, "api_key") or os.environ.get("NETPULSE_API_KEY")
        )
        timeout = timeout if timeout != 30 else get_config_value(config, "timeout", 30)
        driver = driver if driver != "netmiko" else get_config_value(config, "driver", "netmiko")

        # Merge connection args: config file < explicit param
        config_conn_args = get_config_value(config, "connection_args", {})
        if default_connection_args:
            config_conn_args.update(default_connection_args)
        default_connection_args = config_conn_args

        # Pool settings from config
        pool_connections = (
            pool_connections
            if pool_connections != 10
            else get_config_value(config, "pool_connections", 10)
        )
        pool_maxsize = (
            pool_maxsize if pool_maxsize != 200 else get_config_value(config, "pool_maxsize", 200)
        )
        max_retries = (
            max_retries if max_retries != 3 else get_config_value(config, "max_retries", 3)
        )

        # Improved error messages
        if not base_url:
            raise ValueError(
                "base_url is required.\n"
                "  → Set via parameter: NetPulseClient(base_url='http://...')\n"
                "  → Or config file: netpulse.yaml with 'base_url' key\n"
                "  → Or env var: export NETPULSE_URL=http://..."
            )
        if not api_key:
            raise ValueError(
                "api_key is required.\n"
                "  → Set via parameter: NetPulseClient(api_key='...')\n"
                "  → Or config file: netpulse.yaml with 'api_key' key\n"
                "  → Or env var: export NETPULSE_API_KEY=..."
            )

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

    def __enter__(self) -> "NetPulseClient":
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - close connections"""
        self.close()

    def close(self) -> None:
        """Close HTTP connection pool"""
        self._http.close()

    def ping(self) -> bool:
        """Check if NetPulse API is reachable

        Returns:
            True if API is reachable, raises exception otherwise
        """
        try:
            # Use a lightweight endpoint to check connectivity
            self._http.get("/health")
            return True
        except Exception as e:
            raise NetPulseError(f"API health check failed: {e}") from e

    def test_connection(
        self,
        device: str,
        connection_args: Optional[dict] = None,
        driver: Optional[str] = None,
    ) -> "ConnectionTestResult":
        """Test device connection

        Args:
            device: Device IP/hostname
            connection_args: Connection arguments (overrides default_connection_args)
            driver: Driver name (overrides default driver)

        Returns:
            ConnectionTestResult with success, latency, error info
        """
        from .result import ConnectionTestResult
        from datetime import datetime

        use_driver = driver or self.driver
        conn_args = {**self.default_connection_args}
        if connection_args:
            conn_args.update(connection_args)
        conn_args["host"] = device

        payload = {
            "driver": use_driver,
            "connection_args": conn_args,
        }

        try:
            resp = self._http.post("/device/test", json=payload)
            data = resp.get("data", {})

            return ConnectionTestResult(
                success=data.get("success", False),
                host=device,
                latency=data.get("latency"),
                error=data.get("error"),
                driver=use_driver,
                timestamp=datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
                if data.get("timestamp")
                else datetime.now(),
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                host=device,
                latency=None,
                error=str(e),
                driver=use_driver,
                timestamp=datetime.now(),
            )

    def test_connections(
        self,
        devices: List[str],
        connection_args: Optional[dict] = None,
        driver: Optional[str] = None,
    ) -> List["ConnectionTestResult"]:
        """Test multiple device connections

        Args:
            devices: List of device IPs/hostnames
            connection_args: Connection arguments (overrides default_connection_args)
            driver: Driver name (overrides default driver)

        Returns:
            List of ConnectionTestResult
        """
        return [
            self.test_connection(device, connection_args=connection_args, driver=driver)
            for device in devices
        ]

    def run(
        self,
        devices: Union[List[str], str, List[dict]],
        command: Union[List[str], str] = None,
        config: Union[List[str], str] = None,
        mode: Literal["auto", "exec", "bulk"] = "auto",
        ttl: int = 300,
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
        """Execute command or configuration

        Args:
            devices: Device list or single device (IP/hostname or connection_args dict)
            command: Command list or single command (query commands, mutually exclusive with config)
            config: Configuration command list or single command (mutually exclusive with command)
            mode: Execution mode (auto, exec for single device, bulk for multiple devices)
            ttl: Job timeout in seconds
            connection_args: Connection arguments (overrides default_connection_args)
            driver: Driver name (overrides default driver)
            driver_args: Driver-specific parameters (read_timeout, delay_factor, etc.)
            credential: Vault credential reference (name, ref, mount, field_mapping, etc.)
            rendering: Template rendering configuration (name, template, context)
            parsing: Output parsing configuration (name, template, context)
            queue_strategy: Queue strategy (fifo or pinned)
            result_ttl: Result retention time in seconds (60-604800)
            webhook: Webhook callback configuration (url, method, headers, etc.)

        Returns:
            Job or JobGroup instance
        """
        devices = [devices] if isinstance(devices, str) else devices

        if command is not None and config is not None:
            raise ValueError("command and config are mutually exclusive")
        if command is None and config is None:
            raise ValueError("Either command or config must be specified")

        operation = command if command is not None else config
        operation = [operation] if isinstance(operation, str) else operation
        operation_type = "command" if command is not None else "config"

        if not devices:
            raise ValueError("devices cannot be empty")

        conn_args = {**self.default_connection_args}
        if connection_args:
            conn_args.update(connection_args)

        if driver_args is None:
            driver_args = self.DEFAULT_DRIVER_ARGS

        api_mode = self._select_api(devices, mode)
        use_driver = driver or self.driver

        if api_mode == "exec":
            device = devices[0] if isinstance(devices[0], str) else devices[0].get("host")
            return self._call_exec_api(
                device=device,
                operation=operation,
                operation_type=operation_type,
                ttl=ttl,
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
                ttl=ttl,
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
        command: Union[List[str], str],
        ttl: int = 300,
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
            command: Command list or single command
            ttl: Job timeout in seconds
            connection_args: Connection arguments
            driver: Driver name
            driver_args: Driver-specific parameters
            credential: Vault credential reference (name is required)
            parsing: Output parsing configuration
            queue_strategy: Queue strategy
            result_ttl: Result retention time (60-604800 seconds)
            webhook: Webhook callback configuration
        """
        return self.run(
            devices=devices,
            command=command,
            mode="auto",
            ttl=ttl,
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

    def list_jobs(
        self,
        queue: Optional[str] = None,
        status: Optional[str] = None,
        node: Optional[str] = None,
        host: Optional[str] = None,
    ) -> List[Job]:
        """List jobs with optional filters

        Args:
            queue: Filter by queue name (e.g., 'netmiko', 'napalm')
            status: Filter by job status ('queued', 'started', 'finished', 'failed')
            node: Filter by node name
            host: Filter by pinned host name

        Returns:
            List of Job instances
        """
        params = {}
        if queue:
            params["queue"] = queue
        if status:
            params["status"] = status
        if node:
            params["node"] = node
        if host:
            params["host"] = host

        resp = self._http.get("/job", params=params if params else None)
        jobs_data = resp.get("data", []) or []

        return [
            Job(client=self, job_data=job_data, device_name="unknown", commands=[])
            for job_data in jobs_data
        ]

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued job

        Args:
            job_id: Job ID to cancel

        Returns:
            True if cancelled successfully
        """
        resp = self._http.delete("/job", params={"id": job_id})
        cancelled = resp.get("data", []) or []
        return job_id in cancelled

    def cancel_jobs(
        self,
        queue: Optional[str] = None,
        host: Optional[str] = None,
    ) -> List[str]:
        """Cancel multiple queued jobs

        Args:
            queue: Filter by queue name
            host: Filter by pinned host name

        Returns:
            List of cancelled job IDs
        """
        params = {}
        if queue:
            params["queue"] = queue
        if host:
            params["host"] = host

        resp = self._http.delete("/job", params=params if params else None)
        return resp.get("data", []) or []

    def list_workers(
        self,
        queue: Optional[str] = None,
        node: Optional[str] = None,
        host: Optional[str] = None,
    ) -> List[dict]:
        """List workers with optional filters

        Args:
            queue: Filter by queue name
            node: Filter by node name
            host: Filter by pinned host name

        Returns:
            List of worker info dictionaries with keys:
                - name: Worker name
                - status: Worker status ('idle', 'busy', 'suspended')
                - pid: Process ID
                - hostname: Host name
                - queues: List of queue names
                - last_heartbeat: Last heartbeat time
                - birth_at: Worker start time
                - successful_job_count: Successful job count
                - failed_job_count: Failed job count
        """
        params = {}
        if queue:
            params["queue"] = queue
        if node:
            params["node"] = node
        if host:
            params["host"] = host

        resp = self._http.get("/worker", params=params if params else None)
        return resp.get("data", []) or []

    def delete_workers(
        self,
        name: Optional[str] = None,
        queue: Optional[str] = None,
        node: Optional[str] = None,
        host: Optional[str] = None,
    ) -> List[str]:
        """Delete workers with optional filters

        Args:
            name: Worker name to delete
            queue: Filter by queue name
            node: Filter by node name
            host: Filter by pinned host name

        Returns:
            List of deleted worker names
        """
        params = {}
        if name:
            params["name"] = name
        if queue:
            params["queue"] = queue
        if node:
            params["node"] = node
        if host:
            params["host"] = host

        resp = self._http.delete("/worker", params=params if params else None)
        return resp.get("data", []) or []

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

    def _add_optional_params(
        self,
        payload: dict,
        driver_args: Optional[dict] = None,
        credential: Optional[dict] = None,
        rendering: Optional[dict] = None,
        parsing: Optional[dict] = None,
        queue_strategy: Optional[str] = None,
        result_ttl: Optional[int] = None,
        webhook: Optional[dict] = None,
    ) -> dict:
        """Add optional parameters to payload if they are not None

        Args:
            payload: Base payload dictionary
            **kwargs: Optional parameters to add

        Returns:
            Updated payload dictionary
        """
        optional_params = {
            "driver_args": driver_args,
            "credential": credential,
            "rendering": rendering,
            "parsing": parsing,
            "queue_strategy": queue_strategy,
            "result_ttl": result_ttl,
            "webhook": webhook,
        }
        for key, value in optional_params.items():
            if value is not None:
                payload[key] = value
        return payload

    def _call_exec_api(
        self,
        device: str,
        operation: List[str],
        operation_type: str,
        ttl: int,
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
            "ttl": ttl,
        }
        self._add_optional_params(
            payload,
            driver_args=driver_args,
            credential=credential,
            rendering=rendering,
            parsing=parsing,
            queue_strategy=queue_strategy,
            result_ttl=result_ttl,
            webhook=webhook,
        )

        log.debug(f"Calling exec API for device: {device}")
        resp = self._http.post("/device/exec", json=payload)
        job_data = resp["data"]

        return Job(client=self, job_data=job_data, device_name=device, commands=operation)

    def _call_bulk_api(
        self,
        devices: List[Union[str, dict]],
        operation: List[str],
        operation_type: str,
        ttl: int,
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
            "ttl": ttl,
        }
        self._add_optional_params(
            payload,
            driver_args=driver_args,
            credential=credential,
            rendering=rendering,
            parsing=parsing,
            queue_strategy=queue_strategy,
            result_ttl=result_ttl,
            webhook=webhook,
        )

        log.debug(f"Calling bulk API for {len(normalized_devices)} devices")
        resp = self._http.post("/device/bulk", json=payload)

        data = resp["data"]
        if not data:
            raise NetPulseError("Bulk API returned empty data")

        succeeded = data.get("succeeded", [])
        failed = data.get("failed", [])

        # Retry failed devices once if some succeeded
        if failed and succeeded:
            log.info(f"Retrying {len(failed)} failed devices: {failed}")

            # Extract failed device hosts
            failed_hosts = set()
            for item in failed:
                if isinstance(item, str):
                    failed_hosts.add(item)
                elif isinstance(item, dict):
                    failed_hosts.add(item.get("host") or item.get("device", ""))

            # Find devices to retry
            retry_devices = [d for d in normalized_devices if d.get("host") in failed_hosts]

            if retry_devices:
                retry_payload = {**payload, "devices": retry_devices}
                retry_resp = self._http.post("/device/bulk", json=retry_payload)
                retry_data = retry_resp.get("data", {})
                retry_succeeded = retry_data.get("succeeded", [])
                retry_failed = retry_data.get("failed", [])

                if retry_succeeded:
                    succeeded.extend(retry_succeeded)
                    log.info(f"Retry succeeded for {len(retry_succeeded)} devices")

                failed = retry_failed
                if failed:
                    log.warning(f"Still failed after retry: {failed}")

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
