"""
pihole/v6.py

This module implements the Pi-hole v6 API interface, extending the abstract base class.
It contains all HTTP communication logic for authenticating, checking status, updating
 blocking, and logging out from a v6 Pi-hole instance.

Classes:
    PiHoleV6API: Implements Pi-hole API v6 interactions.
"""
import logging
import socket

import requests

from utils.session import get_retrying_session
from .base import PiHoleAPIBase

LOGGER = logging.getLogger(__name__)

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

    @staticmethod
    def _response_preview(response):
        """
        Return a short preview of the response body for logging.
        """
        body = (response.text or "").strip().replace("\n", " ")
        return body[:200] if body else "<empty>"

    def _reset_session(self, reason):
        """
        Recreate the HTTP session after connection-level failures or stale state.
        """
        LOGGER.info("Resetting HTTP session for %s: %s", self.domain, reason)
        self.sid = None
        self.csrf = None
        super().logout()
        self.session = get_retrying_session()

    def _ensure_session(self):
        """
        Lazily recreate the HTTP session if a prior logout cleared it.
        """
        if self.session is None:
            self.session = get_retrying_session()

    def _resolve_domain(self):
        """
        Resolve the configured domain to aid network diagnostics in logs.
        """
        try:
            return socket.gethostbyname_ex(self.domain)[2]
        except OSError as err:
            return [f"<resolution failed: {err}>"]

    def _log_request_failure(self, message, error):
        """
        Log request failures with enough context to diagnose proxy and backend issues.
        """
        response = getattr(error, "response", None)
        request = getattr(error, "request", None)
        LOGGER.warning(
            "%s for %s: %s method=%s url=%s resolved_ips=%s status=%s body=%s",
            message,
            self.domain,
            error,
            getattr(request, "method", "<unknown>"),
            getattr(request, "url", "<unknown>"),
            self._resolve_domain(),
            getattr(response, "status_code", None),
            self._response_preview(response) if response is not None else "<no response>"
        )

    def authenticate(self):
        """
        Obtain authentication session and CSRF token from a Pi-hole v6 instance.
        Initializes self.session for reuse in subsequent calls.

        Returns:
            tuple: (sid, csrf) if successful, (None, None) otherwise.
        """
        self._ensure_session()

        url = f"https://{self.domain}/api/auth"

        try:
            response = self.session.get(url, timeout=5)
        except requests.RequestException as err:
            self._log_request_failure("Pi-hole auth status check failed", err)
            self._reset_session("auth status check request failed")
            response = None

        if response and response.status_code == 200:
            try:
                data = response.json()
                session = data.get("session") or {}
                self.sid = session.get("sid")
                self.csrf = session.get("csrf")
            except ValueError:
                LOGGER.warning(
                    "Pi-hole auth status response for %s was not valid JSON. "
                    "status=%s body=%s",
                    self.domain,
                    response.status_code,
                    self._response_preview(response)
                )
                self.sid = None
                self.csrf = None

            if self.sid and self.csrf:
                return self.sid, self.csrf
        elif response is not None:
            LOGGER.info(
                "Pi-hole auth status for %s did not return an active session. "
                "status=%s body=%s",
                self.domain,
                response.status_code,
                self._response_preview(response)
            )

        payload = {"password": self.token}
        try:
            response = self.session.post(url, json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()
            self.sid = data['session']['sid']
            self.csrf = data['session']['csrf']
            return self.sid, self.csrf
        except ValueError:
            LOGGER.warning(
                "Pi-hole auth response for %s was not valid JSON. status=%s body=%s",
                self.domain,
                response.status_code,
                self._response_preview(response)
            )
            self._reset_session("auth response was not valid JSON")
            return None, None
        except requests.RequestException as e:
            self._log_request_failure("Pi-hole auth failed", e)
            self._reset_session("auth request failed")
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
            data = r.json()
            if not isinstance(data, dict) or "blocking" not in data:
                LOGGER.warning(
                    "Unexpected blocking status payload for %s: %r",
                    self.domain,
                    data
                )
                return None
            return data
        except ValueError:
            LOGGER.warning(
                "Blocking status response for %s was not valid JSON. status=%s body=%s",
                self.domain,
                r.status_code,
                self._response_preview(r)
            )
            return None
        except requests.RequestException as e:
            self._log_request_failure("Failed to get blocking status", e)
            self._reset_session("blocking status request failed")
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
            self._log_request_failure(
                f"Failed to set blocking={enable}",
                e
            )
            self._reset_session(f"set blocking request failed (enable={enable})")
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
        self._ensure_session()
        if self.session and self.sid and self.csrf:
            url = f"https://{self.domain}/api/auth"
            headers = {"X-FTL-SID": self.sid, "X-FTL-CSRF": self.csrf}
            try:
                self.session.delete(url, headers=headers, timeout=3)
            except requests.RequestException as err:
                LOGGER.info("Pi-hole logout failed for %s: %s", self.domain, err)
        self.sid = None
        self.csrf = None
        super().logout()
