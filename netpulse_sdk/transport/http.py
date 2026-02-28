"""
HTTP client wrapper
"""

import logging
from typing import Any, Optional, Union

import httpx

from ..error import AuthError, NetworkError, RequestTimeoutError

log = logging.getLogger(__name__)


class HTTPClient:
    """HTTP client for NetPulse API communication"""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        api_key_name: str = "X-API-KEY",
        timeout: int = 30,
        pool_connections: int = 10,
        pool_maxsize: int = 200,
        max_retries: int = 3,
    ):
        """Initialize HTTP client

        Args:
            base_url: API base URL
            api_key: API key
            api_key_name: API key header name (default: X-API-KEY)
            timeout: Request timeout in seconds
            pool_connections: Number of connection pools (for different hosts)
            pool_maxsize: Maximum connections per pool
            max_retries: Automatic retry count
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_key_name = api_key_name
        self.timeout = timeout
        
        limits = httpx.Limits(
            max_keepalive_connections=pool_connections,
            max_connections=pool_maxsize,
        )
        transport = httpx.HTTPTransport(retries=max_retries, limits=limits)
        
        self.session = httpx.Client(
            base_url=self.base_url,
            headers={api_key_name: api_key},
            timeout=timeout,
            transport=transport,
        )

    def _handle_response(self, response: httpx.Response) -> Union[dict, list]:
        """Handle API response"""
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if response.status_code == 401 or response.status_code == 403:
                raise AuthError(f"API key authentication failed ({self.api_key_name})") from e
            
            # Try to extract detailed error from JSON body
            try:
                error_data = response.json()
                detail = error_data.get("detail")
                if isinstance(detail, list) and detail:
                    # FastAPI validation error
                    msg = "; ".join([f"{d.get('loc', [])}: {d.get('msg')}" for d in detail])
                    raise NetworkError(f"Validation error: {msg}") from e
                elif isinstance(detail, str):
                    raise NetworkError(f"API error: {detail}") from e
            except (ValueError, TypeError, KeyError):
                pass
                
            raise NetworkError(f"HTTP error: {response.status_code}") from e

        if response.status_code == 204:
            return {}

        try:
            return response.json()
        except ValueError as e:
            raise NetworkError("Invalid JSON response") from e

    def get(self, path: str, params: Optional[dict] = None, stream: bool = False) -> Union[dict, list, httpx.Response]:
        """Send GET request"""
        try:
            if stream:
                return self.session.stream("GET", path, params=params)
            response = self.session.get(path, params=params)
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise RequestTimeoutError(f"Request timeout: {path}", url=path) from e
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}") from e

    def post(self, path: str, json: Optional[dict] = None) -> dict:
        """Send POST request"""
        try:
            response = self.session.post(path, json=json)
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise RequestTimeoutError(f"Request timeout: {path}", url=path) from e
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}") from e

    def post_multipart(
        self, 
        path: str, 
        data: Optional[dict] = None, 
        files: Optional[dict] = None,
        content: Any = None,
    ) -> dict:
        """Send multipart POST request"""
        try:
            response = self.session.post(path, data=data, files=files, content=content)
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise RequestTimeoutError(f"Request timeout: {path}", url=path) from e
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}") from e

    def delete(self, path: str, params: Optional[dict] = None) -> Union[dict, list]:
        """Send DELETE request"""
        try:
            response = self.session.delete(path, params=params)
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise RequestTimeoutError(f"Request timeout: {path}", url=path) from e
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}") from e

    def put(self, path: str, json: Optional[dict] = None) -> dict:
        """Send PUT request"""
        try:
            response = self.session.put(path, json=json)
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise RequestTimeoutError(f"Request timeout: {path}", url=path) from e
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}") from e

    def patch(self, path: str, json: Optional[dict] = None) -> dict:
        """Send PATCH request"""
        try:
            response = self.session.patch(path, json=json)
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise RequestTimeoutError(f"Request timeout: {path}", url=path) from e
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}") from e

    def close(self):
        """Close session"""
        self.session.close()
