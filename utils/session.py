"""
utils/session.py

This module provides a utility function to create a requests.Session with retry logic.
It is used to ensure resilient HTTP requests when communicating with Pi-hole APIs.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def get_retrying_session(retries=3, backoff_factor=0.5):
    """
    Create a requests session with retry logic for resilient HTTP requests.

    Args:
        retries (int): Number of retry attempts.
        backoff_factor (float): Backoff factor for retry delays.

    Returns:
        requests.Session: Configured session object.
    """
    status_forcelist = (500, 502, 503, 504, 400)
    allowed_methods = ["GET", "POST"]

    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=allowed_methods,
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    return session
