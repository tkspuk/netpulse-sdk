"""
NetPulse client
"""

import logging
import os
from typing import Callable, List, Literal, Optional, Union

from .error import NetPulseError
from .job import Job, JobGroup
from .result import (
    ConnectionTestResult,
    DetachedTaskInfo,
    DetachedTaskLog,
    JobProgress,
    Result,
    WorkerInfo,
)
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
        timeout: Optional[int] = None,
        driver: Optional[str] = None,
        default_connection_args: Optional[dict] = None,
        pool_connections: Optional[int] = None,
        pool_maxsize: Optional[int] = None,
        max_retries: Optional[int] = None,
        profile: Optional[str] = None,
        config_path: Optional[str] = None,
        enable_mode: bool = False,
        save: bool = False,
        api_key_name: Optional[str] = None,
        default_credential: Optional[dict] = None,
    ):
        """Initialize NetPulse client

        Args:
            base_url: NetPulse API URL. Falls back to config file, then NETPULSE_URL env var.
            api_key: API key. Falls back to config file, then NETPULSE_API_KEY env var.
            timeout: HTTP request timeout in seconds (default 30)
            driver: Default driver (netmiko, napalm, pyeapi, paramiko). Default "netmiko"
            default_connection_args: Default connection arguments (username, password, etc.)
            default_credential: Default Vault credential reference (optional)
            pool_connections: HTTP connection pool count (default 10)
            pool_maxsize: Maximum connections per pool (default 200, increase to 500 for large batches)
            max_retries: HTTP request auto-retry count (default 3)
            profile: Config profile name (default uses 'default' profile)
            config_path: Explicit config file path (optional)
            enable_mode: Default enable mode (Netmiko)
            save: Default save mode (Netmiko)
            api_key_name: API key header name (default: X-API-KEY)
        """
        # Load config file
        from .config import load_config, get_config_value

        config = load_config(config_path=config_path, profile=profile)

        # Priority: explicit param > config file > environment variable > hardcoded default
        base_url = (
            base_url or get_config_value(config, "base_url") or os.environ.get("NETPULSE_URL")
        )
        api_key = (
            api_key or get_config_value(config, "api_key") or os.environ.get("NETPULSE_API_KEY")
        )
        api_key_name = (
            api_key_name
            or get_config_value(config, "api_key_name")
            or os.environ.get("NETPULSE_API_KEY_NAME")
            or "X-API-KEY"
        )
        timeout = timeout if timeout is not None else get_config_value(config, "timeout", 30)
        driver = driver if driver is not None else get_config_value(config, "driver", "netmiko")

        # Merge connection args: config file < explicit param
        config_conn_args = get_config_value(config, "connection_args", {})
        if default_connection_args:
            config_conn_args.update(default_connection_args)
        default_connection_args = config_conn_args

        # Merge credentials: config file < explicit param
        config_credential = get_config_value(config, "credential", {})
        if default_credential:
            config_credential.update(default_credential)
        default_credential = config_credential

        # Pool settings from config (explicit param > config > default)
        pool_connections = (
            pool_connections
            if pool_connections is not None
            else get_config_value(config, "pool_connections", 10)
        )
        pool_maxsize = (
            pool_maxsize
            if pool_maxsize is not None
            else get_config_value(config, "pool_maxsize", 200)
        )
        max_retries = (
            max_retries if max_retries is not None else get_config_value(config, "max_retries", 3)
        )

        # Improved error messages
        if not base_url:
            raise ValueError("base_url is required (pass to client, or set NETPULSE_URL)")
        if not api_key:
            raise ValueError("api_key is required (pass to client, or set NETPULSE_API_KEY)")

        self._http = HTTPClient(
            base_url=base_url,
            api_key=api_key,
            api_key_name=api_key_name,
            timeout=timeout,
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=max_retries,
        )
        self.driver = driver
        self.default_connection_args = default_connection_args or {}
        self.default_credential = default_credential or None
        self.enable_mode = enable_mode
        self.save = save

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
            True if API is reachable, False otherwise.
            Use get_health() if you need error details.
        """
        try:
            self._http.get("/health")
            return True
        except Exception:
            return False

    def test_connection(
        self,
        device: str,
        connection_args: Optional[dict] = None,
        driver: Optional[str] = None,
        credential: Optional[dict] = None,
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
        if credential:
            payload["credential"] = credential

        try:
            resp = self._http.post("/device/test", json=payload)
            # 0.4.0+: resp is ConnectionTestResponse

            # Extract standard fields
            ts_str = resp.get("timestamp")
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")) if ts_str else datetime.now()

            # Flatten 0.4.0+ 'result' object for better SDK experience
            result_inner = resp.get("result") or {}
            # Collect extra fields not already handled as explicit params
            explicit_keys = {"success", "latency", "error", "timestamp", "result", "host", "driver"}
            extra_data = {k: v for k, v in resp.items() if k not in explicit_keys}
            if isinstance(result_inner, dict):
                extra_data.update({k: v for k, v in result_inner.items() if k not in explicit_keys})

            return ConnectionTestResult(
                ok=resp.get("success", False),
                host=device,
                latency=resp.get("latency"),
                error=resp.get("error"),
                driver=use_driver,
                timestamp=ts,
                **extra_data,
            )
        except Exception as e:
            return ConnectionTestResult(
                ok=False,
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
        credential: Optional[dict] = None,
    ) -> List["ConnectionTestResult"]:
        """Test multiple device connections

        Args:
            devices: List of device IPs/hostnames
            connection_args: Connection arguments (overrides default_connection_args)
            driver: Driver name (overrides default driver)
            credential: Vault credential reference

        Returns:
            List of ConnectionTestResult
        """
        import concurrent.futures

        results = [None] * len(devices)
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(devices), 50)) as executor:
            future_to_index = {
                executor.submit(
                    self.test_connection,
                    device,
                    connection_args=connection_args,
                    driver=driver,
                    credential=credential,
                ): idx
                for idx, device in enumerate(devices)
            }

            for future in concurrent.futures.as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    # Create a failed result if something crashed
                    from datetime import datetime
                    from .result import ConnectionTestResult

                    results[idx] = ConnectionTestResult(
                        ok=False,
                        host=devices[idx],
                        error=str(e),
                        driver=driver or self.driver or "unknown",
                        timestamp=datetime.now(),
                    )

        return results

    def run(
        self,
        devices: Union[List[str], str, List[dict]],
        command: Union[List[str], str] = None,
        config: Union[List[str], str] = None,
        mode: Literal["auto", "exec", "bulk"] = "auto",
        ttl: int = 300,
        execution_timeout: Optional[int] = None,
        connection_args: Optional[dict] = None,
        driver: Optional[str] = None,
        driver_args: Optional[dict] = None,
        credential: Optional[dict] = None,
        rendering: Optional[dict] = None,
        parsing: Optional[dict] = None,
        queue_strategy: Optional[Literal["fifo", "pinned"]] = None,
        result_ttl: Optional[int] = None,
        webhook: Optional[dict] = None,
        file_transfer: Optional[dict] = None,
        detach: bool = False,
        push_interval: Optional[int] = None,
        staged_file_id: Optional[str] = None,
        local_upload_file: Optional[str] = None,
        enable_mode: Optional[bool] = None,
        save: Optional[bool] = None,
        callback: Optional[Callable] = None,
        auto_retry: bool = True,
    ) -> Union[Job, JobGroup]:
        """Execute operations on devices (API Mode: config or command)

        This is the primary method for executing tasks. It automatically detects
        whether to use 'config' or 'command' mode based on the input.

        Args:
            auto_retry: Automatically retry devices that fail bulk submission once (default True).
                Set to False to disable silent retries. Retried devices are recorded in
                JobGroup.retried_devices.

        Returns:
            Job or JobGroup instance
        """
        was_list = isinstance(devices, list)
        devices = [devices] if isinstance(devices, str) else devices

        if command is not None and config is not None:
            raise ValueError("command and config are mutually exclusive")

        # Smart detection of operation type
        if config is not None:
            operation = config
            operation_type = "config"
        else:
            operation = command
            operation_type = "command"

        job = self._execute(
            devices=devices,
            operation=operation,
            operation_type=operation_type,
            mode=mode,
            ttl=ttl,
            execution_timeout=execution_timeout,
            connection_args=connection_args,
            driver=driver,
            driver_args=driver_args,
            credential=credential,
            rendering=rendering,
            parsing=parsing,
            queue_strategy=queue_strategy,
            result_ttl=result_ttl,
            webhook=webhook,
            file_transfer=file_transfer,
            detach=detach,
            push_interval=push_interval,
            staged_file_id=staged_file_id,
            local_upload_file=local_upload_file,
            enable_mode=enable_mode if enable_mode is not None else self.enable_mode,
            save=save if save is not None else self.save,
            return_group=was_list or mode == "bulk",
            auto_retry=auto_retry,
        )

        if callback and not detach:
            job.wait(callback=callback)

        return job

    def collect(
        self,
        devices: Union[List[str], str, List[dict]],
        command: Union[List[str], str, None] = None,
        ttl: int = 300,
        execution_timeout: Optional[int] = None,
        connection_args: Optional[dict] = None,
        driver: Optional[str] = None,
        driver_args: Optional[dict] = None,
        credential: Optional[dict] = None,
        rendering: Optional[dict] = None,
        parsing: Optional[dict] = None,
        queue_strategy: Optional[Literal["fifo", "pinned"]] = None,
        result_ttl: Optional[int] = None,
        webhook: Optional[dict] = None,
        file_transfer: Optional[dict] = None,
        detach: bool = False,
        push_interval: Optional[int] = None,
        staged_file_id: Optional[str] = None,
        local_upload_file: Optional[str] = None,
        enable_mode: bool = False,
        save: bool = False,
        callback: Optional[Callable] = None,
    ) -> Union[Job, JobGroup]:
        """Information Gathering and Audit (API Mode: command)

        Strictly for READ-ONLY operations. It forces save=False and enable_mode=False
        by default for safety. Use this for monitoring, audits, and data extraction.

        Args:
            devices: Device list or single device
            command: Command list or single command
            ttl: Job timeout in seconds
            connection_args: Connection arguments
            driver: Driver name
            driver_args: Driver-specific parameters
            credential: Vault credential reference (name is required)
            rendering: Template rendering configuration
            parsing: Output parsing configuration
            queue_strategy: Queue strategy
            result_ttl: Result retention time (60-604800 seconds)
            webhook: Webhook callback configuration
            file_transfer: File transfer configuration
            detach: Run command in background
            push_interval: Interval for incremental webhook log pushes
            staged_file_id: Staged file id
            local_upload_file: Local file to upload
            enable_mode: Default False. Enter privileged mode before execution.
            save: Default False. Save configuration after execution.
            callback: Progress callback function(progress_obj)
        """
        # Enforce read-only constraints
        if command is None and not file_transfer:
            raise ValueError("collect() requires a command.")
        if save:
            raise ValueError("collect() is read-only: save=True is not allowed. Use run() instead.")
        if file_transfer and file_transfer.get("operation") == "upload":
            raise ValueError(
                "collect() is read-only: file upload is not allowed. Use run() instead."
            )

        was_list = isinstance(devices, list)
        job = self._execute(
            devices=devices,
            operation=command,
            operation_type="command",
            ttl=ttl,
            execution_timeout=execution_timeout,
            connection_args=connection_args,
            driver=driver,
            driver_args=driver_args,
            credential=credential,
            rendering=rendering,
            parsing=parsing,
            queue_strategy=queue_strategy,
            result_ttl=result_ttl,
            webhook=webhook,
            file_transfer=file_transfer,
            detach=detach,
            push_interval=push_interval,
            staged_file_id=staged_file_id,
            local_upload_file=local_upload_file,
            enable_mode=enable_mode,
            save=save,
            return_group=was_list,
        )

        if callback and not detach:
            job.wait(callback=callback)

        return job

    def _execute(
        self,
        devices: Union[List[str], str, List[dict]],
        operation: Union[List[str], str] = None,
        operation_type: Literal["command", "config"] = "command",
        mode: Literal["auto", "exec", "bulk"] = "auto",
        ttl: int = 300,
        execution_timeout: Optional[int] = None,
        connection_args: Optional[dict] = None,
        driver: Optional[str] = None,
        driver_args: Optional[dict] = None,
        credential: Optional[dict] = None,
        rendering: Optional[dict] = None,
        parsing: Optional[dict] = None,
        queue_strategy: Optional[Literal["fifo", "pinned"]] = None,
        result_ttl: Optional[int] = None,
        webhook: Optional[dict] = None,
        file_transfer: Optional[dict] = None,
        detach: bool = False,
        push_interval: Optional[int] = None,
        staged_file_id: Optional[str] = None,
        local_upload_file: Optional[str] = None,
        enable_mode: Optional[bool] = None,
        save: Optional[bool] = None,
        callback: Optional[Callable] = None,
        return_group: bool = False,
        auto_retry: bool = True,
    ) -> Union[Job, JobGroup]:
        """Internal execute dispatcher"""
        # 1. Normalize devices
        if isinstance(devices, (str, dict)):
            devices = [devices]

        # 2. Extract driver and connection_args from first device if not provided
        if not driver or not connection_args:
            first_device = devices[0]
            driver = driver or self.driver
            if isinstance(first_device, dict):
                driver = driver or first_device.get("driver")
                connection_args = connection_args or first_device.get("connection_args")

            # Fallback to defaults
            connection_args = (connection_args or self.default_connection_args).copy()

        if not driver:
            raise ValueError("Driver must be specified if no default driver is set")

        # 2.1 Use default credential if not provided
        if credential is None:
            credential = self.default_credential

        # If credentials are provided, remove auth fields from connection_args
        # to avoid validation conflicts in backend.
        if credential and isinstance(connection_args, dict):
            auth_fields = {
                "username",
                "password",
                "secret",
                "key_file",
                "key_filename",
                "pkey",
                "passphrase",
                "token",
            }
            # Only remove if it's actually in auth_fields to keep the dictionary clean
            for field in auth_fields:
                connection_args.pop(field, None)

        # 3. Normalize operation
        if isinstance(operation, str):
            operation = [operation]

        # 4. Use effective enable_mode and save
        eff_enable_mode = enable_mode if enable_mode is not None else self.enable_mode
        eff_save = save if save is not None else self.save

        # 5. Handle directory-style remote_path for uploads
        if local_upload_file and file_transfer and file_transfer.get("operation") == "upload":
            remote_path = file_transfer.get("remote_path")
            if remote_path and (remote_path.endswith("/") or remote_path.endswith("\\")):
                import os

                filename = os.path.basename(local_upload_file)
                # Join path and ensure forward slashes for cross-platform compatibility
                full_remote_path = os.path.join(remote_path, filename).replace("\\", "/")
                file_transfer["remote_path"] = full_remote_path

        # 6. Use Bulk API if multiple devices, otherwise Use Exec API
        api_type = self._select_api(devices, mode)
        if api_type == "bulk":
            return self._call_bulk_api(
                devices=devices,
                operation=operation,
                operation_type=operation_type,
                ttl=ttl,
                connection_args=connection_args or {},
                driver=driver,
                driver_args=driver_args,
                credential=credential,
                rendering=rendering,
                parsing=parsing,
                queue_strategy=queue_strategy,
                result_ttl=result_ttl,
                webhook=webhook,
                file_transfer=file_transfer,
                detach=detach,
                push_interval=push_interval,
                staged_file_id=staged_file_id,
                enable_mode=eff_enable_mode,
                save=eff_save,
                callback=callback,
                auto_retry=auto_retry,
            )
        else:
            device = devices[0]
            device_host = device if isinstance(device, str) else device.get("host")
            job = self._call_exec_api(
                device=device_host,
                operation=operation,
                operation_type=operation_type,
                ttl=ttl,
                execution_timeout=execution_timeout,
                connection_args=connection_args or {},
                driver=driver,
                driver_args=driver_args,
                credential=credential,
                rendering=rendering,
                parsing=parsing,
                queue_strategy=queue_strategy,
                result_ttl=result_ttl,
                webhook=webhook,
                file_transfer=file_transfer,
                detach=detach,
                push_interval=push_interval,
                staged_file_id=staged_file_id,
                enable_mode=eff_enable_mode,
                save=eff_save,
                local_upload_file=local_upload_file,
                callback=callback,
            )
            if return_group:
                from .job import JobGroup

                return JobGroup(jobs=[job])
            return job

    def render_template(
        self,
        template: str,
        context: dict,
        name: str = "jinja2",
        **kwargs,
    ) -> str:
        """Render a configuration template

        Args:
            template: Template content or reference
            context: Template context (variables)
            name: Renderer engine name (default: jinja2)
            **kwargs: Additional parameters for specific renderers
        """
        payload = {
            "name": name,
            "template": template,
            "context": context,
            **kwargs,
        }
        resp = self._http.post("/template/render", json=payload)
        # Backend returns rendered string directly
        if isinstance(resp, str):
            return resp
        # Fallback for dict response (future-proofing)
        return resp.get("rendered", resp) if isinstance(resp, dict) else str(resp)

    def parse_template(
        self,
        output: str,
        name: str = "ttp",
        template: Optional[str] = None,
        **kwargs,
    ) -> Union[dict, list]:
        """Parse device output using templates

        Args:
            output: Raw device output string
            name: Parser engine name (default: ttp)
            template: Optional template content or reference
            **kwargs: Additional parameters like use_ntc_template, ttp_template_args, etc.
        """
        payload = {
            "name": name,
            "context": output,
            **kwargs,
        }
        if template:
            payload["template"] = template

        return self._http.post("/template/parse", json=payload)

    def get_job(self, job_id: str) -> Job:
        """Get Job by ID (GET /jobs/{id})

        Args:
            job_id: Unique job identifier
        """
        resp = self._http.get(f"/jobs/{job_id}")

        # 0.4.0+: Use device_name and command from response if available
        device_name = resp.get("device_name")
        command = resp.get("command")

        # Fallback to results if not in top level
        if not device_name or not command:
            result = resp.get("result")
            if result and result.get("retval"):
                first_res = result["retval"][0]
                if not device_name:
                    device_name = (
                        first_res.get("metadata", {}).get("host")
                        or first_res.get("device_name")
                        or "unknown"
                    )
                if not command:
                    command = [r.get("command") for r in result["retval"] if r.get("command")]

        return Job(
            client=self, job_data=resp, device_name=device_name or "unknown", command=command
        )

    def list_jobs(
        self,
        status: Optional[str] = None,
        queue: Optional[str] = None,
        node: Optional[str] = None,
        host: Optional[str] = None,
    ) -> List[Job]:
        """List jobs with optional filters (GET /jobs)

        Args:
            queue: Filter by queue name
            status: Filter by job status
            node: Filter by node name
            host: Filter by pinned host name
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

        resp = self._http.get("/jobs", params=params if params else None)
        # 0.4.0+: resp is List[JobInResponse]
        return [
            Job(
                client=self,
                job_data=job_data,
                device_name=job_data.get("device_name") or "unknown",
                command=job_data.get("command"),
            )
            for job_data in resp
        ]

    def cancel_job(self, job_id: str) -> bool:
        """Cancel/Delete a job (DELETE /jobs/{id})

        Args:
            job_id: Job ID to cancel
        """
        self._http.delete(f"/jobs/{job_id}")
        # 0.3.x/0.4.0 delete returns success info, commonly 204 or a simple dict
        return True

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

        resp = self._http.delete("/jobs", params=params if params else None)
        return resp

    def list_workers(
        self,
        queue: Optional[str] = None,
        node: Optional[str] = None,
        host: Optional[str] = None,
    ) -> List[WorkerInfo]:
        """List workers with optional filters

        Args:
            queue: Filter by queue name
            node: Filter by node name
            host: Filter by pinned host name

        Returns:
            List of WorkerInfo objects
        """
        params = {}
        if queue:
            params["queue"] = queue
        if node:
            params["node"] = node
        if host:
            params["host"] = host

        resp = self._http.get("/workers", params=params if params else None)
        return [WorkerInfo.model_validate(w) for w in resp]

    def delete_worker(self, name: str) -> bool:
        """Delete a single worker by name (DELETE /workers/{name})

        Args:
            name: Worker name to delete

        Returns:
            True if deleted successfully
        """
        self._http.delete(f"/workers/{name}")
        return True

    def delete_workers(
        self,
        queue: Optional[str] = None,
        node: Optional[str] = None,
        host: Optional[str] = None,
    ) -> list:
        """Delete multiple workers with filters (DELETE /workers)

        Args:
            queue: Filter by queue name
            node: Filter by node name
            host: Filter by pinned host name

        Returns:
            List of deleted worker info
        """
        params = {}
        if queue:
            params["queue"] = queue
        if node:
            params["node"] = node
        if host:
            params["host"] = host

        return self._http.delete("/workers", params=params if params else None)

    # =========================================================================
    # Detached Tasks (Task Recovery)
    # =========================================================================

    def list_detached_tasks(self, status: Optional[str] = None) -> List[DetachedTaskInfo]:
        """List all active detached tasks in the server registry

        Args:
            status: Optional status filter (running, completed, launching)

        Returns:
            List of DetachedTaskInfo objects
        """
        params = {}
        if status:
            params["status"] = status
        resp = self._http.get("/detached-tasks", params=params)
        return [DetachedTaskInfo.model_validate(t) for t in resp]

    def get_detached_task(self, task_id: str, offset: Optional[int] = None) -> "DetachedTaskLog":
        """Query a detached task's logs and status (GET /detached-tasks/{task_id})

        Args:
            task_id: Detached task ID
            offset: Byte offset for incremental reading. Pass DetachedTaskLog.next_offset
                    from the previous call to avoid duplicate log lines.

        Returns:
            DetachedTaskLog with output, is_running, next_offset, and pid.
        """
        params = {}
        if offset is not None:
            params["offset"] = offset
        resp = self._http.get(f"/detached-tasks/{task_id}", params=params)
        return DetachedTaskLog.model_validate(resp)

    def tail_detached_task(
        self,
        task_id: str,
        poll_interval: float = 3.0,
        callback: Optional[Callable] = None,
    ) -> str:
        """Stream incremental logs from a running detached task until it finishes.

        Handles the next_offset loop automatically so callers don't have to.

        Args:
            task_id: Detached task ID (from job.task_id after run(..., detach=True))
            poll_interval: Seconds between polls (default 3.0)
            callback: Optional function(log_chunk: str) called with each new log chunk.
                      If not provided, chunks are silently collected.

        Returns:
            Full accumulated log output.

        Example::

            job = np.run("10.1.1.1", "apt-get upgrade -y", detach=True)
            full_log = np.tail_detached_task(
                job.task_id,
                callback=lambda chunk: print(chunk, end="", flush=True),
            )
        """
        import time

        offset = 0
        full_output = []

        while True:
            snap = self.get_detached_task(task_id, offset=offset)
            if snap.output:
                full_output.append(snap.output)
                if callback:
                    callback(snap.output)
            offset = snap.next_offset

            if not snap.is_running:
                break

            time.sleep(poll_interval)

        return "".join(full_output)

    def cancel_detached_task(self, task_id: str) -> bool:
        """Terminate a detached task on the remote host

        Args:
            task_id: Detached task ID

        Returns:
            True if cancelled successfully
        """
        self._http.delete(f"/detached-tasks/{task_id}")
        return True

    def discover_detached_tasks(
        self,
        device: str,
        driver: str = "paramiko",
        connection_args: Optional[dict] = None,
        credential: Optional[dict] = None,
    ) -> List[DetachedTaskInfo]:
        """Scan a device for background tasks and sync them into the server registry

        Args:
            device: Device IP/hostname
            driver: Driver name (default: paramiko)
            connection_args: Connection arguments
            credential: Optional credential configuration

        Returns:
            List of newly discovered DetachedTaskInfo objects
        """
        payload = {
            "driver": driver,
            "connection_args": {
                **(connection_args or self.default_connection_args),
                "host": device,
            },
        }
        if credential:
            payload["credential"] = credential

        resp = self._http.post("/detached-tasks/discover", json=payload)
        if isinstance(resp, list):
            return [DetachedTaskInfo.model_validate(t) for t in resp]
        return resp

    def discover_jobs(self, status: str = "running") -> List[Job]:
        """Recover Job objects for existing detached tasks"""
        tasks = self.list_detached_tasks(status=status)
        jobs = []
        for task in tasks:
            if not task.task_id:
                continue

            job_data = {
                "id": f"task_{task.task_id}",
                "status": "started" if task.status == "running" else "finished",
                "task_id": task.task_id,
                "created_at": task.created_at,
                "command": task.command,
                "driver": task.driver,
            }

            device_name = task.host or "recovered_host"
            command = task.command or []

            jobs.append(Job(self, job_data, device_name, command))
        return jobs

    def get_health(self) -> dict:
        """Get system health status"""
        resp = self._http.get("/health")
        return resp

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

    def _add_optional_params(self, payload: dict, **kwargs) -> dict:
        """Add non-None kwargs to payload"""
        for key, value in kwargs.items():
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
        execution_timeout: Optional[int] = None,
        driver_args: Optional[dict] = None,
        credential: Optional[dict] = None,
        rendering: Optional[dict] = None,
        parsing: Optional[dict] = None,
        queue_strategy: Optional[str] = None,
        result_ttl: Optional[int] = None,
        webhook: Optional[dict] = None,
        file_transfer: Optional[dict] = None,
        detach: Optional[bool] = None,
        push_interval: Optional[int] = None,
        staged_file_id: Optional[str] = None,
        local_upload_file: Optional[str] = None,
        enable_mode: Optional[bool] = None,
        save: Optional[bool] = None,
        callback: Optional[Callable] = None,
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
        if execution_timeout is not None:
            payload["execution_timeout"] = execution_timeout

        self._add_optional_params(
            payload,
            driver_args=driver_args,
            credential=credential,
            rendering=rendering,
            parsing=parsing,
            queue_strategy=queue_strategy,
            result_ttl=result_ttl,
            webhook=webhook,
            file_transfer=file_transfer,
            detach=detach,
            push_interval=push_interval,
            staged_file_id=staged_file_id,
            enable_mode=enable_mode,
            save=save,
        )

        if local_upload_file is not None:
            import json
            import os

            if not os.path.exists(local_upload_file):
                raise ValueError(f"File {local_upload_file} does not exist")

            # Wrap file for progress tracking
            class ProgressFile:
                def __init__(self, file_obj, callback=None):
                    self.file_obj = file_obj
                    self.callback = callback
                    self.size = os.path.getsize(local_upload_file)
                    self.read_count = 0

                def read(self, size=-1):
                    data = self.file_obj.read(size)
                    if data:
                        self.read_count += len(data)
                        if self.callback:
                            self.callback(self.read_count, self.size)
                    return data

                def __iter__(self):
                    return self

                def __next__(self):
                    data = self.read(8192)
                    if not data:
                        raise StopIteration
                    return data

                def close(self):
                    self.file_obj.close()

            file_cb = None
            if callback and not detach:

                def file_cb(cur, tot):
                    return callback(JobProgress(total=tot, completed=cur, failed=0, running=1))

            with open(local_upload_file, "rb") as f:
                log.debug(
                    f"Calling multipart exec API for device: {device} with file: {local_upload_file}"
                )

                pf = ProgressFile(f, callback=file_cb) if file_cb else f

                resp = self._http.post_multipart(
                    "/device/exec",
                    data={"request": json.dumps(payload)},
                    files={"file": (os.path.basename(local_upload_file), pf)},
                )
        else:
            log.debug(f"Calling exec API for device: {device}")
            resp = self._http.post("/device/exec", json=payload)

        # 0.4.0: resp is JobInResponse
        return Job(client=self, job_data=resp, device_name=device, command=operation)

    def _call_bulk_api(
        self,
        devices: List[Union[str, dict]],
        operation: List[str],
        operation_type: str,
        ttl: int,
        connection_args: dict,
        driver: str,
        execution_timeout: Optional[int] = None,
        driver_args: Optional[dict] = None,
        credential: Optional[dict] = None,
        rendering: Optional[dict] = None,
        parsing: Optional[dict] = None,
        queue_strategy: Optional[str] = None,
        result_ttl: Optional[int] = None,
        webhook: Optional[dict] = None,
        file_transfer: Optional[dict] = None,
        detach: Optional[bool] = None,
        push_interval: Optional[int] = None,
        staged_file_id: Optional[str] = None,
        enable_mode: Optional[bool] = None,
        save: Optional[bool] = None,
        callback: Optional[Callable] = None,
        auto_retry: bool = True,
    ) -> JobGroup:
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
        if execution_timeout is not None:
            payload["execution_timeout"] = execution_timeout

        self._add_optional_params(
            payload,
            driver_args=driver_args,
            credential=credential,
            rendering=rendering,
            parsing=parsing,
            queue_strategy=queue_strategy,
            result_ttl=result_ttl,
            webhook=webhook,
            file_transfer=file_transfer,
            detach=detach,
            push_interval=push_interval,
            staged_file_id=staged_file_id,
            enable_mode=enable_mode,
            save=save,
        )

        log.debug(f"Calling bulk API for {len(normalized_devices)} devices")
        resp = self._http.post("/device/bulk", json=payload)

        # 0.4.0: resp is BatchSubmitJobResponse {succeeded, failed}
        succeeded = resp.get("succeeded", [])
        failed = resp.get("failed", [])
        retried_hosts: List[str] = []

        # Retry failed devices once if auto_retry is enabled and some succeeded
        if auto_retry and failed and succeeded:
            # Extract failed device hosts
            failed_hosts = set()
            for item in failed:
                if isinstance(item, str):
                    failed_hosts.add(item)
                elif isinstance(item, dict):
                    failed_hosts.add(item.get("host") or item.get("device", ""))

            retry_devices = [d for d in normalized_devices if d.get("host") in failed_hosts]

            if retry_devices:
                retried_hosts = [d.get("host", "") for d in retry_devices]
                log.info(f"Auto-retrying {len(retry_devices)} failed devices: {retried_hosts}")

                retry_payload = {**payload, "devices": retry_devices}
                retry_resp = self._http.post("/device/bulk", json=retry_payload)
                retry_succeeded = retry_resp.get("succeeded", [])
                retry_failed = retry_resp.get("failed", [])

                if retry_succeeded:
                    succeeded.extend(retry_succeeded)
                    log.info(f"Retry succeeded for {len(retry_succeeded)} devices")

                failed = retry_failed

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
                Job(client=self, job_data=job_data, device_name=device_name, command=operation)
            )

        return JobGroup(jobs=jobs, failed_devices=failed, retried_devices=retried_hosts)

    def fetch_staged_file(
        self, file_id: str, dest_path: str, callback: Optional[Callable] = None
    ) -> None:
        """Fetch a staged file from Netpulse storage.

        Args:
            file_id: The ID of the staged file or a full download URL.
            dest_path: Local path where the file should be saved
            callback: Progress callback function(completed_bytes, total_bytes)
        """
        import os

        # If file_id is already a full URL, use download_file
        if file_id.startswith("http"):
            return self.download_file(file_id, dest_path, callback)

        # Use the internal session for consistent headers and base_url handling
        url = f"{self._http.base_url}/storage/fetch/{file_id}"
        with self._http.session.stream("GET", url) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0

            os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
            with open(dest_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if callback:
                        callback(downloaded, total_size)

    def download_file(self, url: str, dest_path: str, callback: Optional[Callable] = None) -> None:
        """Download file from a full URL (e.g. from Result.download_url)

        Args:
            url: Full download URL
            dest_path: Local path to save
            callback: Progress callback
        """
        import os
        from urllib.parse import urlparse

        full_url = url
        if not url.startswith("http"):
            full_url = f"{self._http.base_url}/{url.lstrip('/')}"
        else:
            # Handle internal k8s URLs by routing through base_url if it looks like a storage fetch
            parsed = urlparse(url)
            if "/storage/fetch/" in parsed.path:
                base_parsed = urlparse(self._http.base_url)
                if parsed.netloc != base_parsed.netloc:
                    # Keep the full path, just swap the host to our gateway
                    full_url = f"{self._http.base_url}/{parsed.path.lstrip('/')}"

        with self._http.session.stream("GET", full_url) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0

            os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
            with open(dest_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if callback:
                        callback(downloaded, total_size)

    # =========================================================================
    # File Transfer Shortcuts (Paramiko / Netmiko)
    # =========================================================================

    def upload(
        self,
        device: str,
        local_path: str,
        remote_path: str,
        connection_args: Optional[dict] = None,
        driver: Optional[str] = None,
        ttl: int = 300,
        callback: Optional[Callable] = None,
    ) -> Result:
        """Upload a local file to a remote device.

        Shortcut for run() with file_transfer operation='upload'.
        Supported drivers: paramiko (SFTP), netmiko (SCP).

        Args:
            device: Device IP/hostname
            local_path: Local file path to upload
            remote_path: Remote destination path (directory ending with '/' is supported)
            connection_args: Connection arguments (overrides defaults)
            driver: Driver name (overrides default)
            ttl: Job timeout in seconds
            callback: Progress callback function(completed_bytes, total_bytes)

        Returns:
            Result of the upload operation

        Example::

            np.upload("10.1.1.30", "./script.py", "/tmp/script.py")
        """
        job = self.run(
            devices=device,
            local_upload_file=local_path,
            file_transfer={"operation": "upload", "remote_path": remote_path},
            connection_args=connection_args,
            driver=driver or self.driver,
            ttl=ttl,
        )
        job.wait(callback=callback)
        return job.first()

    def download(
        self,
        device: str,
        remote_path: str,
        local_path: str,
        connection_args: Optional[dict] = None,
        driver: Optional[str] = None,
        ttl: int = 300,
        callback: Optional[Callable] = None,
    ) -> Result:
        """Download a file from a remote device to local.

        Shortcut that handles the full download flow:
        run() → wait() → fetch staged file.
        Supported drivers: paramiko (SFTP), netmiko (SCP).

        Args:
            device: Device IP/hostname
            remote_path: Remote file path to download
            local_path: Local destination path
            connection_args: Connection arguments (overrides defaults)
            driver: Driver name (overrides default)
            ttl: Job timeout in seconds
            callback: Progress callback function(completed_bytes, total_bytes)

        Returns:
            Result of the download operation

        Example::

            np.download("10.1.1.30", "/etc/hostname", "./hostname.txt")
        """
        from .error import NetPulseError

        job = self.run(
            devices=device,
            file_transfer={"operation": "download", "remote_path": remote_path},
            connection_args=connection_args,
            driver=driver or self.driver,
            ttl=ttl,
        )
        job.wait()
        result = job.first()

        if not result.ok:
            raise NetPulseError(
                f"Download failed for {device}:{remote_path} — {result.error or result.stderr}"
            )
        if not result.download_url:
            raise NetPulseError(
                f"Download job succeeded but no download_url returned for {device}:{remote_path}"
            )
        self.fetch_staged_file(result.download_url, local_path, callback=callback)
        return result
