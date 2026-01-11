"""
Job and JobGroup implementation
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterator, List, Optional, Union

from .error import Error, JobFailedError
from .result import JobProgress, Result

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
    def wait(self, timeout: Optional[int] = None) -> "JobInterface":
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
        commands: Optional[List[str]] = None,
    ):
        """Initialize Job

        Args:
            client: NetPulseClient instance
            job_data: JobInResponse data from API
            device_name: Device name (for Result generation)
            commands: Command list executed (for Result generation)
        """
        self._client = client
        self._data = job_data
        self._device_name = device_name
        self._commands = commands or []

    @property
    def id(self) -> str:
        return self._data["id"]

    @property
    def status(self) -> str:
        """Job status: queued, started, finished, failed, canceled"""
        return self._data.get("status", "unknown")

    def refresh(self) -> "Job":
        """Refresh job status"""
        resp = self._client._http.get("/job", params={"id": self.id})
        if resp["data"] and len(resp["data"]) > 0:
            self._data = resp["data"][0]
        return self

    def wait(self, timeout: Optional[int] = None, poll_interval: float = 0.5) -> "Job":
        """Wait for job completion (with exponential backoff)

        Args:
            timeout: Timeout in seconds, None for infinite wait
            poll_interval: Initial polling interval in seconds, default 0.5
        """
        start_time = time.time()
        interval = poll_interval
        max_interval = 5.0
        backoff_factor = 1.5

        while not self.is_done():
            if timeout and (time.time() - start_time) > timeout:
                raise JobFailedError(f"Job {self.id} wait timeout", job_id=self.id)

            time.sleep(interval)
            self.refresh()

            interval = min(interval * backoff_factor, max_interval)

        return self

    def cancel(self) -> None:
        """Cancel job (only queued status can be canceled)"""
        if self.status != "queued":
            log.warning(f"Job {self.id} status is {self.status}, cannot cancel")
            return

        self._client._http.delete("/job", params={"id": self.id})
        self.refresh()

    def progress(self) -> JobProgress:
        """Get progress

        Single job progress:
        - total = command count
        - completed/failed/running determined by status
        """
        total = max(len(self._commands), 1)

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
        """Parse JobInResponse into standard Result list

        Backend response format:
        {
            "result": {
                "type": 1,  # SUCCESSFUL
                "retval": {
                    "show version": "output1",
                    "show ip int br": "output2"
                },
                "error": {"type": "...", "message": "..."}
            }
        }
        """
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

        if isinstance(retval, dict) and retval:
            for cmd, output in retval.items():
                results.append(
                    Result(
                        job_id=self.id,
                        device_id=self._device_name,
                        device_name=self._device_name,
                        command=cmd,
                        stdout=str(output) if ok else "",
                        stderr="" if ok else str(output),
                        ok=ok,
                        duration_ms=duration_ms,
                        error=error,
                    )
                )
        elif isinstance(retval, list) and retval:
            for idx, output in enumerate(retval):
                cmd = self._commands[idx] if idx < len(self._commands) else f"command_{idx + 1}"
                results.append(
                    Result(
                        job_id=self.id,
                        device_id=self._device_name,
                        device_name=self._device_name,
                        command=cmd,
                        stdout=str(output) if ok else "",
                        stderr="" if ok else str(output),
                        ok=ok,
                        duration_ms=duration_ms,
                        error=error,
                    )
                )
        elif isinstance(retval, str):
            cmd = self._commands[0] if self._commands else "unknown"
            results.append(
                Result(
                    job_id=self.id,
                    device_id=self._device_name,
                    device_name=self._device_name,
                    command=cmd,
                    stdout=retval if ok else "",
                    stderr="" if ok else retval,
                    ok=ok,
                    duration_ms=duration_ms,
                    error=error,
                )
            )

        # If no results generated yet (empty retval, None, or failed job), create error result
        if not results:
            commands_to_report = self._commands if self._commands else ["unknown"]
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
        """Stream results (with exponential backoff)

        Single job stream waits for completion then returns all results

        Args:
            poll_interval: Initial polling interval in seconds, default 0.5
        """
        interval = poll_interval
        max_interval = 5.0
        backoff_factor = 1.5

        while not self.is_done():
            time.sleep(interval)
            self.refresh()
            interval = min(interval * backoff_factor, max_interval)

        yield from self.results()

    def is_done(self) -> bool:
        """Whether job is done (finished, failed, canceled)"""
        return self.status in ["finished", "failed", "canceled"]

    def __iter__(self) -> Iterator[Result]:
        """Support direct iteration, auto-wait and return results"""
        self.wait()
        return iter(self.results())

    def __getitem__(self, key) -> List[Result]:
        """Support index or device name access

        Args:
            key: Index or device name
        """
        self.wait()
        results = self.results()
        if isinstance(key, int):
            return [results[key]]
        elif isinstance(key, str):
            return [r for r in results if r.device_name == key]
        else:
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

    def first(self) -> Optional[Result]:
        """Get the first result (convenience for single device scenarios)

        Returns:
            First Result or None if no results
        """
        self.wait()
        results = self.results()
        return results[0] if results else None

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
    def outputs(self) -> dict:
        """Get all outputs as a dictionary

        Returns:
            {device_name: stdout} for single-command jobs
            {device_name: {command: stdout}} for multi-command jobs
        """
        self.wait()
        results = self.results()
        if len(results) == 1:
            return {results[0].device_name: results[0].stdout}
        else:
            output_dict = {}
            for r in results:
                if r.device_name not in output_dict:
                    output_dict[r.device_name] = {}
                output_dict[r.device_name][r.command] = r.stdout
            return output_dict

    def __repr__(self):
        return f"Job(id={self.id}, status={self.status})"


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
        - All finished → finished
        - Any failed → partial_failed
        - Any running → running
        - Other → mixed
        """
        statuses = [job.status for job in self.jobs]

        if all(s == "finished" for s in statuses):
            return "finished"
        elif any(s == "failed" for s in statuses):
            return "partial_failed"
        elif any(s in ["queued", "started"] for s in statuses):
            return "running"
        else:
            return "mixed"

    def refresh(self) -> "JobGroup":
        """Refresh all job statuses"""
        self._results_cache = None
        for job in self.jobs:
            job.refresh()
        return self

    def wait(self, timeout: Optional[int] = None, poll_interval: float = 0.5) -> "JobGroup":
        """Wait for all jobs to complete (with exponential backoff)

        Args:
            timeout: Timeout in seconds
            poll_interval: Initial polling interval in seconds, default 0.5
        """
        start_time = time.time()
        interval = poll_interval
        max_interval = 5.0
        backoff_factor = 1.5

        while not self.is_done():
            if timeout and (time.time() - start_time) > timeout:
                raise JobFailedError("JobGroup wait timeout")

            time.sleep(interval)
            self.refresh()

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

    def stream(self, poll_interval: float = 0.5) -> Iterator[Result]:
        """Stream results (with exponential backoff)

        Implementation:
        1. Track returned results (deduplicate by job_id + command)
        2. Periodically refresh all jobs
        3. Yield newly completed results
        4. Continue until all jobs complete

        Args:
            poll_interval: Initial polling interval in seconds, default 0.5
        """
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

    def first(self) -> Optional[Result]:
        """Get the first result (convenience for single device scenarios)

        Returns:
            First Result or None if no results
        """
        self.wait()
        results = self.results()
        return results[0] if results else None

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
    def outputs(self) -> dict:
        """Get all outputs as a dictionary

        Returns:
            {device_name: stdout} for single-command jobs
            {device_name: {command: stdout}} for multi-command jobs
        """
        self.wait()
        result_dict = {}
        for r in self.results():
            if len(self.jobs[0]._commands) <= 1:
                # Single command: {device: stdout}
                result_dict[r.device_name] = r.stdout
            else:
                # Multi command: {device: {cmd: stdout}}
                if r.device_name not in result_dict:
                    result_dict[r.device_name] = {}
                result_dict[r.device_name][r.command] = r.stdout
        return result_dict

    def __repr__(self):
        return f"JobGroup(jobs={len(self.jobs)}, status={self.status})"
