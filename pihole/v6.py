"""
pihole/v6.py

This module implements the Pi-hole v6 API interface, extending the abstract base class.
It contains all HTTP communication logic for authenticating, checking status, updating
 blocking, and logging out from a v6 Pi-hole instance.

Classes:
    PiHoleV6API: Implements Pi-hole API v6 interactions.
"""
import requests

from utils.session import get_retrying_session
from .base import PiHoleAPIBase

class PiHoleV6API(PiHoleAPIBase):
    """
    Pi-hole API v6 implementation.

    Implements authentication, status checking, blocking toggling, and logging out for
     Pi-hole v6 instances.
    """

    def __init__(self, domain, token):
        """
        Initialize the PiHoleV6API instance.

        Args:
            domain (str): The domain of the Pi-hole instance.
            token (str): The token or password for authentication.
        """
        super().__init__(domain, token)
        self.sid = None
        self.csrf = None
        self.session = get_retrying_session()


    def authenticate(self):
        """
        Obtain authentication session and CSRF token from a Pi-hole v6 instance.
        Initializes self.session for reuse in subsequent calls.

        Returns:
            tuple: (sid, csrf) if successful, (None, None) otherwise.
        """

        url = f"https://{self.domain}/api/auth"

        response = self.session.get(url, timeout=5)

        if response.status_code == 200:

            data = response.json()
            self.sid = data['session']['sid']
            self.csrf = data['session']['csrf']

            if(self.sid and self.csrf):
                return self.sid, self.csrf

        payload = {"password": self.token}
        try:
            response = self.session.post(url, json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()
            self.sid = data['session']['sid']
            self.csrf = data['session']['csrf']
            return self.sid, self.csrf
        except requests.RequestException as e:
            print(f"Auth failed for {self.domain}: {e}")
            self.logout()
            return None, None

    def get_blocking_status(self):
        """
        Retrieve the current blocking status from the Pi-hole v6 instance.

        Returns:
            Any: The blocking status as returned by the Pi-hole v6 API, or None on error.
        """
        sid, csrf = self.authenticate()
        if not sid or not csrf:
            return None
        url = f"https://{self.domain}/api/dns/blocking"
        headers = {"X-FTL-SID": sid, "X-FTL-CSRF": csrf}
        try:
            r = self.session.get(url, headers=headers, timeout=5)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            print(f"Failed to get blocking status for {self.domain}: {e}")
            return None

    def set_blocking(self, enable: bool, duration=None):
        """
        Enable or disable blocking on the Pi-hole v6 instance.

        Args:
            enable (bool): True to enable blocking, False to disable.
            duration (optional): For temporary enablement, the duration.

        Returns:
            tuple: (success: bool, message: str)
        """
        sid, csrf = self.authenticate()
        if not sid or not csrf:
            return False, "Authentication failed"
        url = f"https://{self.domain}/api/dns/blocking/?blocking={'true' if enable else 'false'}"
        payload = {"blocking": enable}
        payload["timer"] = duration
        headers = {"X-FTL-SID": sid, "X-FTL-CSRF": csrf}
        try:
            r = self.session.post(url, headers=headers, json=payload, timeout=5)
            r.raise_for_status()
            return True, "Success"
        except requests.RequestException as e:
            return False, str(e)

    def logout(self):
        """
        Log out the session from the Pi-hole v6 instance, close HTTP session, and reset credentials.

        Args:
            *args: Ignored, provided for interface compatibility.
            **kwargs: Ignored, provided for interface compatibility.

        Returns:
            None
        """
        if self.session and self.sid and self.csrf:
            url = f"https://{self.domain}/api/auth"
            headers = {"X-FTL-SID": self.sid, "X-FTL-CSRF": self.csrf}
            try:
                self.session.delete(url, headers=headers, timeout=3)
            except requests.RequestException:
                pass
        self.sid = None
        self.csrf = None
        super().logout()
