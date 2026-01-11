"""
HTTP client wrapper
"""

import logging
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..error import AuthError, NetworkError, RequestTimeoutError

log = logging.getLogger(__name__)


class HTTPClient:
    """HTTP client for NetPulse API communication"""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 30,
        pool_connections: int = 10,
        pool_maxsize: int = 200,
        max_retries: int = 3,
    ):
        """Initialize HTTP client

        Args:
            base_url: API base URL
            api_key: API key
            timeout: Request timeout in seconds
            pool_connections: Number of connection pools (for different hosts)
            pool_maxsize: Maximum connections per pool
            max_retries: Automatic retry count
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()

        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "DELETE"],
        )

        adapter = HTTPAdapter(
            pool_connections=pool_connections, pool_maxsize=pool_maxsize, max_retries=retry_strategy
        )

        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({"X-API-KEY": api_key})

    def _handle_response(self, response: requests.Response) -> dict:
        """Handle API response"""
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401 or response.status_code == 403:
                raise AuthError("API key authentication failed") from e
            raise NetworkError(f"HTTP error: {response.status_code}") from e

        try:
            data = response.json()
        except ValueError as e:
            raise NetworkError("Invalid JSON response") from e

        # NetPulse API unified response format: {code, message, data}
        if data.get("code") != 200 and data.get("code") != 201:
            raise NetworkError(f"API error: {data.get('message', 'Unknown error')}")

        return data

    def get(self, path: str, params: Optional[dict] = None) -> dict:
        """Send GET request"""
        url = f"{self.base_url}{path}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            return self._handle_response(response)
        except requests.exceptions.Timeout as e:
            raise RequestTimeoutError(f"Request timeout: {url}", url=url) from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network request failed: {str(e)}") from e

    def post(self, path: str, json: Optional[dict] = None) -> dict:
        """Send POST request"""
        url = f"{self.base_url}{path}"
        try:
            response = self.session.post(url, json=json, timeout=self.timeout)
            return self._handle_response(response)
        except requests.exceptions.Timeout as e:
            raise RequestTimeoutError(f"Request timeout: {url}", url=url) from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network request failed: {str(e)}") from e

    def delete(self, path: str, params: Optional[dict] = None) -> dict:
        """Send DELETE request"""
        url = f"{self.base_url}{path}"
        try:
            response = self.session.delete(url, params=params, timeout=self.timeout)
            return self._handle_response(response)
        except requests.exceptions.Timeout as e:
            raise RequestTimeoutError(f"Request timeout: {url}", url=url) from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network request failed: {str(e)}") from e

    def put(self, path: str, json: Optional[dict] = None) -> dict:
        """Send PUT request"""
        url = f"{self.base_url}{path}"
        try:
            response = self.session.put(url, json=json, timeout=self.timeout)
            return self._handle_response(response)
        except requests.exceptions.Timeout as e:
            raise RequestTimeoutError(f"Request timeout: {url}", url=url) from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network request failed: {str(e)}") from e

    def patch(self, path: str, json: Optional[dict] = None) -> dict:
        """Send PATCH request"""
        url = f"{self.base_url}{path}"
        try:
            response = self.session.patch(url, json=json, timeout=self.timeout)
            return self._handle_response(response)
        except requests.exceptions.Timeout as e:
            raise RequestTimeoutError(f"Request timeout: {url}", url=url) from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network request failed: {str(e)}") from e

    def close(self):
        """Close session"""
        self.session.close()
