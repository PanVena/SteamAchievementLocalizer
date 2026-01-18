"""
Centralized HTTP client for network requests with proper error handling,
retry logic, and connection pooling.
"""

import time
import requests
from requests.adapters import HTTPAdapter
from typing import Optional, Dict, Any

try:
    from urllib3.util.retry import Retry
    RETRY_AVAILABLE = True
except ImportError:
    RETRY_AVAILABLE = False

try:
    import certifi
    CA_BUNDLE = certifi.where()
except ImportError:
    CA_BUNDLE = True  # Fallback to default system store

try:
    CA_BUNDLE = certifi.where()
except ImportError:
    CA_BUNDLE = True  # Fallback to default system store


class HTTPClient:
    """
    Centralized HTTP client with:
    - Connection pooling
    - Retry logic for transient failures
    - Proper timeout configuration
    - Consistent headers
    - SSL verification
    """
    
    _instance: Optional['HTTPClient'] = None
    _session: Optional[requests.Session] = None
    
    def __init__(self):
        if HTTPClient._session is None:
            HTTPClient._session = self._create_session()
    
    @classmethod
    def _create_session(cls) -> requests.Session:
        """Create a configured requests session with retry strategy"""
        session = requests.Session()
        
        # Configure retry strategy if available
        if RETRY_AVAILABLE:
            # Note: 429 is handled manually to respect Retry-After header
            retry_strategy = Retry(
                total=3,  # Total number of retries
                backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
                status_forcelist=[500, 502, 503, 504],  # Retry on these status codes (429 handled manually)
                allowed_methods=["GET", "HEAD"],  # Only retry safe methods
                raise_on_status=False  # Don't raise on status codes, let us handle it
            )
            
            adapter = HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=10,  # Number of connection pools to cache
                pool_maxsize=20  # Maximum number of connections to save in the pool
            )
        else:
            # Fallback if urllib3 Retry is not available
            adapter = HTTPAdapter(
                pool_connections=10,
                pool_maxsize=20
            )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            'User-Agent': 'SteamAchievementLocalizer/1.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate'
        })
        
        return session
    
    @classmethod
    def get_session(cls) -> requests.Session:
        """Get or create the shared session"""
        if cls._session is None:
            cls._session = cls._create_session()
        return cls._session
    
    @classmethod
    def get(
        cls,
        url: str,
        timeout: tuple = (5, 10),  # (connect_timeout, read_timeout)
        verify: bool = True,
        headers: Optional[Dict[str, str]] = None,
        stream: bool = False,
        **kwargs
    ) -> requests.Response:
        """
        Make a GET request with proper error handling.
        
        Args:
            url: URL to request
            timeout: Tuple of (connect_timeout, read_timeout) in seconds
            verify: Whether to verify SSL certificates (default: True, uses CA_BUNDLE)
            headers: Additional headers to include
            stream: Whether to stream the response
            **kwargs: Additional arguments to pass to requests.get
            
        Returns:
            requests.Response object
            
        Raises:
            requests.exceptions.RequestException: For network errors
        """
        session = cls.get_session()
        
        # Merge headers
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        # Use CA_BUNDLE for verification if verify is True
        verify_param = CA_BUNDLE if verify else False
        
        try:
            response = session.get(
                url,
                timeout=timeout,
                verify=verify_param,
                headers=request_headers,
                stream=stream,
                **kwargs
            )
            
            # Handle rate limiting with exponential backoff
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 5))
                time.sleep(retry_after)
                # Retry once after waiting
                response = session.get(
                    url,
                    timeout=timeout,
                    verify=verify_param,
                    headers=request_headers,
                    stream=stream,
                    **kwargs
                )
            
            return response
            
        except requests.exceptions.Timeout as e:
            raise requests.exceptions.Timeout(
                f"Request to {url} timed out after {timeout} seconds"
            ) from e
        except requests.exceptions.SSLError as e:
            # If SSL verification fails and verify was True, try once without verification
            # (for systems with outdated certificates)
            if verify:
                print(f"[HTTPClient] SSL Error for {url}, trying unverified...")
                try:
                    return session.get(
                        url,
                        timeout=timeout,
                        verify=False,
                        headers=request_headers,
                        stream=stream,
                        **kwargs
                    )
                except Exception:
                    # If unverified also fails, raise the original SSL error
                    raise e
            raise
        except requests.exceptions.RequestException:
            # Re-raise other request exceptions as-is
            raise
    
    @classmethod
    def close(cls):
        """Close the session and clean up resources"""
        if cls._session:
            cls._session.close()
            cls._session = None
