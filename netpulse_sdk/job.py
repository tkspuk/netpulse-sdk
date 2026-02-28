"""
Job and JobGroup implementation
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterator, List, Optional, Union

from .error import Error, JobFailedError
from .result import JobProgress, Result
from datetime import datetime

if TYPE_CHECKING:
    from .client import NetPulseClient

log = logging.getLogger(__name__)


class JobInterface(ABC):
    """Unified interface for Job and JobGroup"""

    @property
    @abstractmethod
    def id(self) -> Union[str, List[str]]:
        """Job ID"""
        pass

    @property
    @abstractmethod
    def status(self) -> str:
        """Job status"""
        pass

    @abstractmethod
    def wait(
        self, 
        timeout: Optional[int] = None, 
        poll_interval: float = 0.5, 
        callback: Optional[Callable] = None
    ) -> "JobInterface":
        """Wait for job completion"""
        pass

    @abstractmethod
    def refresh(self) -> "JobInterface":
        """Refresh job status"""
        pass

    @abstractmethod
    def cancel(self) -> None:
        """Cancel job"""
        pass

    @abstractmethod
    def progress(self) -> JobProgress:
        """Get progress"""
        pass

    @abstractmethod
    def results(self) -> List[Result]:
        """Get all results"""
        pass

    @abstractmethod
    def stream(self, poll_interval: float = 0.5) -> Iterator[Result]:
        """Stream results"""
        pass

    @abstractmethod
    def is_done(self) -> bool:
        """Whether job is done"""
        pass


class Job(JobInterface):
    """Single job wrapper"""

    def __init__(
        self,
        client: "NetPulseClient",
        job_data: dict,
        device_name: str,
        command: Optional[List[str]] = None,
    ):
        """Initialize Job

        Args:
            client: NetPulseClient instance
            job_data: JobInResponse data from API
            device_name: Device name (for Result generation)
            command: Command list executed (for fallback reference)
        """
        self._client = client
        self._data = job_data
        self._device_name = device_name
        self._command = command or []

    @property
    def id(self) -> str:
        return self._data["id"]

    @property
    def status(self) -> str:
        """Job status (queued, started, finished, failed, canceled)"""
        return self._data.get("status", "unknown")

    @property
    def task_id(self) -> Optional[str]:
        """Detached task ID if detach=True was used"""
        return self._data.get("task_id")

    @property
    def device_name(self) -> str:
        """Target device name"""
        return self._device_name

    @property
    def command(self) -> List[str]:
        """Executed command list"""
        return self._command

    @property
    def duration(self) -> Optional[float]:
        """Execution duration in seconds"""
        return self._data.get("duration")

    @property
    def queue_time(self) -> Optional[float]:
        """Time spent in queue in seconds"""
        return self._data.get("queue_time")

    @property
    def created_at(self) -> Optional[datetime]:
        """Job creation time"""
        return self._parse_time(self._data.get("created_at"))

    @property
    def enqueued_at(self) -> Optional[datetime]:
        """Job enqueue time"""
        return self._parse_time(self._data.get("enqueued_at"))

    @property
    def started_at(self) -> Optional[datetime]:
        """Job start time"""
        return self._parse_time(self._data.get("started_at"))

    @property
    def ended_at(self) -> Optional[datetime]:
        """Job end time"""
        return self._parse_time(self._data.get("ended_at"))

    @property
    def queue(self) -> Optional[str]:
        """Queue name the job was processed in"""
        return self._data.get("queue")

    @property
    def worker(self) -> Optional[str]:
        """Worker name that executed the job"""
        return self._data.get("worker")

    def _parse_time(self, time_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO format time string"""
        if not time_str:
            return None
        try:
            return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        except ValueError:
            return None

    def refresh(self) -> "Job":
        """Refresh job status from API (GET /jobs/{id})
        
        Fetches the latest job data including status and results.
        """
        resp = self._client._http.get(f"/jobs/{self.id}")
        # 0.4.0+: resp is JobInResponse
        self._data = resp
        return self

    def wait(
        self, 
        timeout: Optional[int] = None, 
        poll_interval: float = 0.5, 
        callback: Optional[Callable] = None
    ) -> "Job":
        """Wait for job completion by polling GET /jobs/{id}
        
        Args:
            timeout: Maximum wait time in seconds (None for infinite)
            poll_interval: Polling frequency in seconds (default 0.5)
            callback: Optional progress callback function(JobProgress)
        """
        start_time = time.time()
        interval = poll_interval
        max_interval = 5.0
        backoff_factor = 1.5

        if callback:
            callback(self.progress())

        while not self.is_done():
            if timeout and (time.time() - start_time) > timeout:
                raise JobFailedError(f"Job {self.id} timed out", job_id=self.id)

            time.sleep(interval)
            self.refresh()
            
            if callback:
                callback(self.progress())

            interval = min(interval * backoff_factor, max_interval)

        return self

    def cancel(self) -> None:
        """Cancel job (only queued status can be canceled)"""
        if self.status != "queued":
            log.warning(f"Job {self.id} status is {self.status}, cannot cancel")
            return

        self._client._http.delete(f"/jobs/{self.id}")
        self.refresh()

    def progress(self) -> JobProgress:
        """Get progress

        Single job progress:
        - total = command count
        - completed/failed/running determined by status
        """
        total = max(len(self._command), 1)

        if self.status == "finished":
            return JobProgress(total=total, completed=total, failed=0, running=0)
        elif self.status == "failed":
            return JobProgress(total=total, completed=0, failed=total, running=0)
        else:
            return JobProgress(total=total, completed=0, failed=0, running=total)

    def results(self) -> List[Result]:
        """Parse job results into standard Result list"""
        if not self.is_done():
            return []

        return self._parse_results()

    def _parse_results(self) -> List[Result]:
        """Convert JobInResponse to list of Result objects"""
        results = []

        result_data = self._data.get("result")
        if not result_data:
            return results

        retval = result_data.get("retval")
        error_data = result_data.get("error")
        duration_ms = int((self._data.get("duration") or 0) * 1000)

        ok = self.status == "finished" and result_data.get("type") == 1

        error = None
        if error_data:
            message = error_data.get("message", "Unknown error")

            if "Pattern not detected" in message or "pattern" in message.lower():
                message = (
                    f"Device prompt detection failed. "
                    f"This usually happens when device response is slow or hostname changed. "
                    f"Try increasing read_timeout and delay_factor in driver_args. "
                    f"Original error: {message}"
                )

            error = Error(
                type=error_data.get("type", "unknown"),
                message=message,
                retryable=self._is_retryable_error(error_data.get("type")),
            )

        if isinstance(retval, list) and retval:
            for idx, item in enumerate(retval):
                if isinstance(item, dict):
                    # Netpulse 0.4.0+ DriverExecutionResult format
                    cmd = item.get("command") or (self._command[idx] if idx < len(self._command) else f"command_{idx + 1}")
                    stdout = str(item.get("stdout", ""))
                    stderr = str(item.get("stderr", ""))
                    exit_status = item.get("exit_status", 0)
                    download_url = item.get("download_url")
                    metadata = item.get("metadata", {})
                    parsed = item.get("parsed")
                    
                    # Set command-specific success
                    cmd_ok = ok
                    if exit_status != 0 or stderr:
                        cmd_ok = False
                        
                    # Effective device name
                    eff_device_name = metadata.get("host") or self._device_name
                    
                    results.append(
                        Result(
                            job_id=self.id,
                            device_id=eff_device_name,
                            device_name=eff_device_name,
                            command=cmd,
                            stdout=stdout,
                            stderr=stderr,
                            ok=cmd_ok,
                            duration_ms=duration_ms,
                            exit_status=exit_status,
                            download_url=download_url,
                            metadata=metadata,
                            parsed=parsed,
                            error=error,
                        )
                    )

        # If no results generated yet (empty retval, None, or failed job), create error result
        if not results:
            commands_to_report = self._command if self._command else ["unknown"]
            for cmd in commands_to_report:
                error_msg = "Job failed with no output"
                if error:
                    error_msg = error.message
                elif not ok:
                    error_msg = f"Job {self.status} with empty result"

                results.append(
                    Result(
                        job_id=self.id,
                        device_id=self._device_name,
                        device_name=self._device_name,
                        command=cmd,
                        stdout="",
                        stderr=error_msg,
                        ok=ok,
                        duration_ms=duration_ms,
                        error=error,
                    )
                )

        return results

    def _is_retryable_error(self, error_type: str) -> bool:
        """Check if error is retryable"""
        retryable_types = {"timeout", "network", "connection"}
        return error_type.lower() in retryable_types

    def stream(self, poll_interval: float = 0.5) -> Iterator[Result]:
        """Stream results (blocks until completion)"""
        self.wait(poll_interval=poll_interval)
        yield from self.results()

    def is_done(self) -> bool:
        """Whether job is done (finished, failed, canceled)"""
        from .enums import JobStatus
        return self.status in [JobStatus.FINISHED, JobStatus.FAILED, JobStatus.CANCELED]

    def __iter__(self) -> Iterator[Result]:
        """Support direct iteration, auto-wait and return results"""
        self.wait()
        return iter(self.results())

    def __len__(self) -> int:
        """Return number of results"""
        self.wait()
        return len(self.results())

    def __getitem__(self, key: Union[int, str]) -> Union[Result, List[Result]]:
        """Access results by index or command pattern

        Args:
            key: int returns single Result, str returns list of Results matching command pattern
        """
        self.wait()
        results = self.results()
        if isinstance(key, int):
            return results[key]
        elif isinstance(key, str):
            # Match by device name or command substring
            return [r for r in results if key == r.device_name or key in r.command]
        raise TypeError(f"Index must be int or str, not {type(key)}")

    def to_dict(self) -> dict:
        """Convert to dictionary

        Returns:
            {device_name: [Result, ...]}
        """
        self.wait()
        return {self._device_name: self.results()}

    def succeeded(self) -> List[Result]:
        """Get all task-completed results (includes device errors)"""
        self.wait()
        return [r for r in self.results() if r.ok]

    def failed(self) -> List[Result]:
        """Get all task-failed results"""
        self.wait()
        return [r for r in self.results() if not r.ok]

    def truly_succeeded(self) -> List[Result]:
        """Get truly successful results (task completed AND device has no errors)"""
        self.wait()
        return [r for r in self.results() if r.is_success]

    def device_errors(self) -> List[Result]:
        """Get device error results (task completed but device returned errors)"""
        self.wait()
        return [r for r in self.results() if r.ok and r.has_device_error()]



    @property
    def all_ok(self) -> bool:
        """Check if all results are successful

        Returns:
            True if all results have ok=True
        """
        self.wait()
        results = self.results()
        return len(results) > 0 and all(r.ok for r in results)

    @property
    def stdout(self) -> str:
        """Get consolidated standard output (only non-empty results)"""
        self.wait()
        return "\n".join(r.stdout for r in self.results() if r.stdout.strip())

    @property
    def stderr(self) -> str:
        """Get consolidated standard error (only non-empty results)"""
        self.wait()
        return "\n".join(r.stderr for r in self.results() if r.stderr.strip())

    @property
    def parsed(self) -> Dict[str, Any]:
        """Get parsed data as a dictionary {command: parsed_data}"""
        self.wait()
        return {r.command: r.parsed for r in self.results()}

    @property
    def stdout_dict(self) -> Dict[str, str]:
        """Get raw standard output mapping {command: stdout}"""
        self.wait()
        return {r.command: r.stdout for r in self.results()}

    @property
    def stderr_dict(self) -> Dict[str, str]:
        """Get raw standard error mapping {command: stderr}"""
        self.wait()
        return {r.command: r.stderr for r in self.results()}



    @property
    def text(self) -> str:
        """Get human-friendly formatted output with command headers

        Unlike stdout (raw concatenation), text adds separators for readability.
        """
        self.wait()
        sections = []
        for r in self.results():
            content = r.stdout if r.stdout.strip() else "(no output)"
            sections.append(f"--- {r.command} ---\n{content}")
        return "\n".join(sections)

    @property
    def failed_commands(self) -> List[str]:
        """Get a list of commands that failed in this job"""
        self.wait()
        return [r.command for r in self.results() if not r.ok]

    def to_json(self) -> str:
        """Convert all results to JSON string"""
        import json
        return json.dumps([r.to_dict() for r in self.results()], indent=2)

    def raise_on_error(self) -> "Job":
        """Raise JobFailedError if any command failed. Returns self for chaining.

        Usage::

            job = np.run("10.1.1.1", config=cmds).raise_on_error()
            # If we get here, everything succeeded
        """
        self.wait()
        if not self.all_ok:
            failed = self.failed_commands
            raise JobFailedError(
                f"Job {self.id} failed: {len(failed)} command(s) failed: {failed}",
                job_id=self.id,
            )
        return self

    def summary(self) -> str:
        """Get a human-readable one-line summary of job execution"""
        self.wait()
        results = self.results()
        ok_count = sum(1 for r in results if r.ok)
        total = len(results)
        dur = f" in {self.duration:.1f}s" if self.duration else ""
        status = "✓ ALL OK" if self.all_ok else f"✗ {total - ok_count}/{total} FAILED"
        return f"Job({self.id[:8]}...) {self.device_name} [{status}] {total} cmd(s){dur}"

    def __bool__(self) -> bool:
        """Allow natural truthiness: `if job:` returns True when all_ok"""
        self.wait()
        return self.all_ok

    def __repr__(self):
        cmd_count = len(self._command) if self._command else "?"
        dur = f", duration={self.duration:.1f}s" if self.duration else ""
        return f"Job(id={self.id[:8]}..., device={self._device_name}, cmds={cmd_count}, status={self.status}{dur})"


class JobGroup(JobInterface):
    """Multiple job aggregation manager"""

    def __init__(self, jobs: List[Job], failed_devices: Optional[List] = None):
        """Initialize JobGroup

        Args:
            jobs: Job list
            failed_devices: List of devices that failed to submit (may contain error info)
        """
        if not jobs:
            raise ValueError("JobGroup requires at least one Job")
        self.jobs = jobs
        self.failed_devices = failed_devices or []
        self._results_cache = None

    @property
    def id(self) -> List[str]:
        """Return all Job IDs"""
        return [job.id for job in self.jobs]

    @property
    def status(self) -> str:
        """Aggregated status:
        - All finished -> finished
        - Any failed -> partial_failed
        - Any running -> running
        - Other -> mixed
        """
        statuses = [job.status for job in self.jobs]
        from .enums import JobStatus

        if all(s == JobStatus.FINISHED for s in statuses):
            return "finished"
        elif any(s == JobStatus.FAILED for s in statuses):
            return "partial_failed"
        elif any(s in [JobStatus.QUEUED, JobStatus.STARTED] for s in statuses):
            return "running"
        else:
            return "mixed"

    def refresh(self) -> "JobGroup":
        """Refresh all job statuses concurrently (GET /jobs/{id} for each job)"""
        import concurrent.futures

        self._results_cache = None

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(self.jobs), 50)) as executor:
            list(executor.map(lambda j: j.refresh(), self.jobs))

        return self

    def wait(
        self, 
        timeout: Optional[int] = None, 
        poll_interval: float = 0.5, 
        callback: Optional[Callable] = None
    ) -> "JobGroup":
        """Wait for all jobs to complete by polling GET /jobs/{id}"""
        start_time = time.time()
        interval = poll_interval
        max_interval = 5.0
        backoff_factor = 1.5

        if callback:
            callback(self.progress())

        while not self.is_done():
            if timeout and (time.time() - start_time) > timeout:
                raise JobFailedError("JobGroup wait timeout")

            time.sleep(interval)
            self.refresh()
            
            if callback:
                callback(self.progress())

            interval = min(interval * backoff_factor, max_interval)

        return self

    def cancel(self) -> None:
        """Cancel all jobs"""
        for job in self.jobs:
            try:
                job.cancel()
            except Exception as e:
                log.warning(f"Failed to cancel Job {job.id}: {e}")

    def progress(self) -> JobProgress:
        """Aggregated progress statistics

        total = sum of all job totals (device count × command count)
        completed/failed/running aggregated from all jobs
        """
        total = 0
        completed = 0
        failed = 0
        running = 0

        for job in self.jobs:
            job_progress = job.progress()
            total += job_progress.total
            completed += job_progress.completed
            failed += job_progress.failed
            running += job_progress.running

        return JobProgress(
            total=total,
            completed=completed,
            failed=failed,
            running=running,
        )

    def results(self) -> List[Result]:
        """Aggregate results from all jobs

        Uses caching when all jobs are done to avoid redundant API calls.
        """
        # Return cached results if available and all jobs are done
        if self._results_cache is not None and self.is_done():
            return self._results_cache

        all_results = []
        for job in self.jobs:
            all_results.extend(job.results())

        # Cache results when all jobs are done
        if self.is_done():
            self._results_cache = all_results

        return all_results

    def submission_failures(self) -> List[dict]:
        """Get devices that failed at the submission stage
        
        Returns:
            List of {"host": ..., "reason": ...} dicts
        """
        return self.failed_devices

    def stream(self, poll_interval: float = 0.5) -> Iterator[Result]:
        """Stream results as they complete"""
        seen = set()
        interval = poll_interval
        max_interval = 5.0
        backoff_factor = 1.5

        while not self.is_done():
            self.refresh()

            for result in self.results():
                key = (result.job_id, result.command)
                if key not in seen:
                    seen.add(key)
                    yield result

            time.sleep(interval)
            interval = min(interval * backoff_factor, max_interval)

        for result in self.results():
            key = (result.job_id, result.command)
            if key not in seen:
                seen.add(key)
                yield result

    def is_done(self) -> bool:
        """Whether all jobs are done"""
        return all(job.is_done() for job in self.jobs)

    def __iter__(self) -> Iterator[Result]:
        """Support direct iteration, auto-stream for batch jobs"""
        return self.stream()

    def __len__(self) -> int:
        """Return number of jobs in the group"""
        return len(self.jobs)

    def __getitem__(self, device_name: str) -> List[Result]:
        """Support dictionary access by device name

        Args:
            device_name: Device name or IP

        Returns:
            All Result list for the device
        """
        self.wait()
        return [r for r in self.results() if r.device_name == device_name]

    def to_dict(self) -> dict:
        """Convert to dictionary for device name access

        Returns:
            {device_name: [Result, ...], ...}
        """
        self.wait()
        result_dict = {}
        for result in self.results():
            if result.device_name not in result_dict:
                result_dict[result.device_name] = []
            result_dict[result.device_name].append(result)
        return result_dict

    def succeeded(self) -> List[Result]:
        """Get all task-completed results (includes device errors)

        Returns:
            List of task-completed Result objects
        """
        self.wait()
        return [r for r in self.results() if r.ok]

    def failed(self) -> List[Result]:
        """Get all task-failed results

        Returns:
            List of task-failed Result objects
        """
        self.wait()
        return [r for r in self.results() if not r.ok]

    def truly_succeeded(self) -> List[Result]:
        """Get truly successful results (task completed AND device has no errors)

        Returns:
            List of truly successful Result objects
        """
        self.wait()
        return [r for r in self.results() if r.is_success]

    def device_errors(self) -> List[Result]:
        """Get device error results (task completed but device returned errors)

        Returns:
            List of device error Result objects
        """
        self.wait()
        return [r for r in self.results() if r.ok and r.has_device_error()]



    @property
    def all_ok(self) -> bool:
        """Check if all results are successful

        Returns:
            True if all results have ok=True
        """
        self.wait()
        results = self.results()
        return len(results) > 0 and all(r.ok for r in results)

    @property
    def stdout(self) -> Dict[str, str]:
        """Get standard output as a dictionary {device_name: consolidated_stdout}"""
        self.wait()
        result_dict = {}
        for r in self.results():
            if r.device_name not in result_dict:
                result_dict[r.device_name] = []
            if r.stdout.strip():
                result_dict[r.device_name].append(r.stdout)
        return {k: "\n".join(v) for k, v in result_dict.items()}

    @property
    def stderr(self) -> Dict[str, str]:
        """Get standard error as a dictionary {device_name: consolidated_stderr}"""
        self.wait()
        result_dict = {}
        for r in self.results():
            if r.device_name not in result_dict:
                result_dict[r.device_name] = []
            if r.stderr.strip():
                result_dict[r.device_name].append(r.stderr)
        return {k: "\n".join(v) for k, v in result_dict.items()}

    @property
    def parsed(self) -> Dict[str, Dict[str, Any]]:
        """Get all parsed data as a nested dictionary {device_name: {command: parsed_data}}"""
        self.wait()
        result_dict = {}
        for r in self.results():
            if r.device_name not in result_dict:
                result_dict[r.device_name] = {}
            result_dict[r.device_name][r.command] = r.parsed
        return result_dict

    @property
    def stdout_dict(self) -> Dict[str, Dict[str, str]]:
        """Get raw standard output as a nested dictionary {device_name: {command: stdout}}"""
        self.wait()
        result_dict = {}
        for r in self.results():
            if r.device_name not in result_dict:
                result_dict[r.device_name] = {}
            result_dict[r.device_name][r.command] = r.stdout
        return result_dict

    @property
    def stderr_dict(self) -> Dict[str, Dict[str, str]]:
        """Get raw standard error as a nested dictionary {device_name: {command: stderr}}"""
        self.wait()
        result_dict = {}
        for r in self.results():
            if r.device_name not in result_dict:
                result_dict[r.device_name] = {}
            result_dict[r.device_name][r.command] = r.stderr
        return result_dict



    @property
    def text(self) -> str:
        """Get consolidated execution logs from all jobs in the group"""
        self.wait()
        sections = []
        for job in self.jobs:
            header = f"=== Device: {job.device_name} (Job: {job.id}) ==="
            sections.append(f"{header}\n{job.text}")
        return "\n\n".join(sections)

    @property
    def failed_commands(self) -> Dict[str, List[str]]:
        """Get a dictionary mapping device names to their failed commands"""
        self.wait()
        return {j.device_name: j.failed_commands for j in self.jobs if not j.all_ok}

    def to_json(self) -> str:
        """Convert all results to JSON string"""
        import json
        return json.dumps([r.to_dict() for r in self.results()], indent=2)

    @property
    def devices(self) -> List[str]:
        """Get list of all device names in this group"""
        return [j.device_name for j in self.jobs]

    def raise_on_error(self) -> "JobGroup":
        """Raise JobFailedError if any device had failures. Returns self for chaining.

        Usage::

            group = np.run(devices, command="show version").raise_on_error()
            # If we get here, all devices succeeded
        """
        self.wait()
        if not self.all_ok:
            failed = self.failed_commands
            failed_devices = list(failed.keys())
            raise JobFailedError(
                f"JobGroup failed: {len(failed_devices)} device(s) had errors: {failed_devices}",
            )
        return self

    def summary(self) -> str:
        """Get a human-readable multi-line summary of group execution"""
        self.wait()
        lines = [f"JobGroup: {len(self.jobs)} device(s), status={self.status}"]
        for job in self.jobs:
            lines.append(f"  {job.summary()}")
        return "\n".join(lines)

    def __bool__(self) -> bool:
        """Allow natural truthiness: `if group:` returns True when all_ok"""
        self.wait()
        return self.all_ok



    def __repr__(self):
        devices = ", ".join(j.device_name for j in self.jobs[:3])
        if len(self.jobs) > 3:
            devices += f", ... (+{len(self.jobs) - 3})"
        return f"JobGroup(devices=[{devices}], jobs={len(self.jobs)}, status={self.status})"
