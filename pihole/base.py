"""
pihole/base.py

This module defines the abstract base class for interacting with Pi-hole API instances.
It provides the interface for all Pi-hole API version implementations, ensuring consistent
 interaction and enabling version-specific adapters.

Classes:
    PiHoleAPIBase: Abstract base class for Pi-hole API implementations.
"""

from abc import ABC, abstractmethod

class PiHoleAPIBase(ABC):
    """
    Abstract base for Pi-hole API access. Allows different API versions to implement this interface.

    Args:
        domain (str): The domain or IP of the Pi-hole instance.
        token (str): The authentication token or password for the Pi-hole instance.
    """

    def __init__(self, domain, token):
        """
        Initialize the PiHoleAPIBase instance.

        Args:
            domain (str): The domain of the Pi-hole instance.
            token (str): The token or password for authentication.
        """
        self.domain = domain
        self.token = token
        self.session = None  # HTTP session, managed by authenticate() and logout()

    def __del__(self):
        """
        Destructor to ensure the session is closed if not already done.
        """
        self.logout()

    @abstractmethod
    def authenticate(self):
        """
        Authenticate with the Pi-hole instance, initialize and store self.session,
        and return authentication credentials.

        Returns:
            tuple: (sid, csrf) session ID and CSRF token, or (None, None) on failure.
        """

    @abstractmethod
    def get_blocking_status(self):
        """
        Retrieve the current blocking status from the Pi-hole instance.

        Returns:
            Any: The current blocking status, as defined by the API version.
        """

    @abstractmethod
    def set_blocking(self, enable: bool, duration=None):
        """
        Enable or disable blocking on the Pi-hole instance.

        Args:
            enable (bool): True to enable blocking, False to disable.
            duration (optional): For temporary enabling/disabling, the duration value.

        Returns:
            tuple: (success:boolean, message:str)
        """

    def logout(self):
        """
        Clean up the session and perform logout if required by the API.
        Safe to call multiple times.

        Args:
            *args: Ignored, provided for interface compatibility.
            **kwargs: Ignored, provided for interface compatibility.
        """
        if self.session:
            try:
                self.session.close()
            except (AttributeError, TypeError):
                pass
            self.session = None
