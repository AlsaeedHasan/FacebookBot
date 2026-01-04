"""
Proxy Manager for DataImpulse Residential Proxies

This module provides automated proxy management for Facebook accounts.
It generates unique session-based proxies from DataImpulse Residential Proxy service.
"""

import os
import random
import string
from dataclasses import dataclass
from typing import Optional

from seleface.logger import Logger


@dataclass
class ProxyConfig:
    """Configuration for DataImpulse proxy connection"""

    username: str
    password: str
    host: str = "gw.dataimpulse.com"
    port: int = 823


class ProxyManager:
    """
    Manages proxy allocation for Facebook accounts using DataImpulse Residential Proxies.

    Each account gets a unique sticky session to maintain the same IP address
    across multiple requests, which is crucial for avoiding detection.

    DataImpulse proxy format:
    - Host: gw.dataimpulse.com:823
    - Username: user__sessid.{random_string}
    - Password: PASSWORD

    Final proxy string format:
    http://user__sessid.{random_string}:PASSWORD@gw.dataimpulse.com:823
    """

    logger = Logger.get_logger("seleface.proxy_manager")

    def __init__(self, config: Optional[ProxyConfig] = None):
        """
        Initialize ProxyManager with DataImpulse credentials.

        Credentials can be provided via:
        1. ProxyConfig object
        2. Environment variables: DATAIMPULSE_USERNAME, DATAIMPULSE_PASSWORD

        Args:
            config: Optional ProxyConfig with credentials and settings
        """
        if config:
            self.username = config.username
            self.password = config.password
            self.host = config.host
            self.port = config.port
        else:
            # Load from environment variables
            self.username = os.environ.get("DATAIMPULSE_USERNAME", "")
            self.password = os.environ.get("DATAIMPULSE_PASSWORD", "")
            self.host = os.environ.get("DATAIMPULSE_HOST", "gw.dataimpulse.com")
            self.port = int(os.environ.get("DATAIMPULSE_PORT", "823"))

        if not self.username or not self.password:
            self.logger.warning(
                "DataImpulse credentials not configured. "
                "Set DATAIMPULSE_USERNAME and DATAIMPULSE_PASSWORD environment variables "
                "or provide a ProxyConfig object."
            )

    def _generate_session_id(self, length: int = 8) -> str:
        """
        Generate a unique random session ID for sticky sessions.

        Args:
            length: Length of the random string (default: 8)

        Returns:
            str: Unique random session identifier
        """
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def _build_username_string(self, session_id: str) -> str:
        """
        Build the DataImpulse username string with session parameter.

        Format: user__sessid.{random_string}

        Args:
            session_id: The session identifier for sticky sessions

        Returns:
            str: Formatted username string
        """
        return f"{self.username}__sessid.{session_id}"

    def get_new_proxy(self, account_id: Optional[str] = None) -> str:
        """
        Generate a new proxy string for an account.

        Creates a unique sticky session proxy that maintains the same IP
        for all requests from this account. This is critical for Facebook
        automation to avoid detection.

        Args:
            account_id: Optional account identifier (e.g., email) for logging purposes

        Returns:
            str: Formatted proxy string ready for use with Selenium
                 Format: http://user__sessid.{random_string}:password@gw.dataimpulse.com:823

        Raises:
            ValueError: If DataImpulse credentials are not configured

        Example:
            >>> manager = ProxyManager()
            >>> proxy = manager.get_new_proxy("user@example.com")
            >>> print(proxy)
            'http://myuser__sessid.ab12cd34:mypass@gw.dataimpulse.com:823'
        """
        if not self.username or not self.password:
            raise ValueError(
                "DataImpulse credentials not configured. "
                "Please set DATAIMPULSE_USERNAME and DATAIMPULSE_PASSWORD environment variables."
            )

        session_id = self._generate_session_id()
        formatted_username = self._build_username_string(session_id)

        proxy_string = (
            f"http://{formatted_username}:{self.password}@{self.host}:{self.port}"
        )

        self.logger.info(
            f"Generated proxy for account '{account_id}' with session '{session_id}'"
        )
        self.logger.debug(f"Proxy host: {self.host}:{self.port}")

        return proxy_string

    def get_proxy_for_selenium(self, account_id: Optional[str] = None) -> dict:
        """
        Get proxy configuration dict suitable for Selenium Chrome options.

        Args:
            account_id: Optional account identifier for logging purposes

        Returns:
            dict: Proxy configuration with 'proxy_string' and 'auth' keys
        """
        session_id = self._generate_session_id()
        formatted_username = self._build_username_string(session_id)

        proxy_string = (
            f"http://{formatted_username}:{self.password}@{self.host}:{self.port}"
        )

        return {
            "proxy_string": proxy_string,
            "host": self.host,
            "port": self.port,
            "username": formatted_username,
            "password": self.password,
        }

    def is_configured(self) -> bool:
        """
        Check if proxy manager has valid credentials configured.

        Returns:
            bool: True if credentials are set, False otherwise
        """
        return bool(self.username and self.password)

    @classmethod
    def from_env(cls) -> "ProxyManager":
        """
        Create a ProxyManager instance from environment variables.

        Environment variables:
        - DATAIMPULSE_USERNAME: DataImpulse account username
        - DATAIMPULSE_PASSWORD: DataImpulse account password
        - DATAIMPULSE_HOST: Proxy host (default: gw.dataimpulse.com)
        - DATAIMPULSE_PORT: Proxy port (default: 823)

        Returns:
            ProxyManager: Configured proxy manager instance
        """
        return cls()
