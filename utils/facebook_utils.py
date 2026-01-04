import json
import os
import pickle
import time
import uuid
from io import BytesIO
from threading import Thread
from time import sleep
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from PIL import Image
from selenium.common.exceptions import WebDriverException

from seleface import Client
from seleface.logger import Logger
from seleface.utils.proxy_manager import ProxyManager


class FacebookUtils:
    """Utility class for Facebook operations with Anti-Detect support"""

    # Maximum retry attempts for browser initialization (IP Kill Switch recovery)
    MAX_CLIENT_INIT_RETRIES = 3

    def __init__(
        self,
        logger: Optional[Logger] = None,
        proxy: Optional[str] = None,
        account_id: Optional[str] = None,
        optimize_bandwidth: bool = True,
        load_images: bool = False,
    ):
        """Initialize Facebook utilities with Anti-Detect capabilities

        Args:
            logger: Custom logger instance (optional)
            proxy: Proxy string (http://user:pass@host:port) for this session
            account_id: Account identifier for profile isolation
            optimize_bandwidth: Block CSS/fonts to save bandwidth (default: True)
            load_images: Allow images to load (default: False for bandwidth saving)
        """
        self.client = None
        self.logger = logger or Logger.get_logger("facebook_utils")
        self.current_account = None
        self._proxy = proxy
        self._account_id = account_id
        self._optimize_bandwidth = optimize_bandwidth
        self._load_images = load_images

    def _init_client_safe(
        self,
        headless: bool = True,
        enable_mobile_emulation: bool = False,
        proxy: Optional[str] = None,
        account_id: Optional[str] = None,
        optimize_bandwidth: bool = True,
        load_images: bool = False,
    ) -> None:
        """
        Safely initialize the Client with retry logic for IP Kill Switch recovery.

        This method handles ConnectionError exceptions raised by the Client's
        IP validation (Kill Switch). If a proxy leak is detected, it will:
        1. Kill the failed browser instance
        2. Wait briefly for cleanup
        3. Retry initialization with a fresh browser

        Args:
            headless: Run browser in headless mode
            enable_mobile_emulation: Enable mobile emulation
            proxy: Proxy string (http://user:pass@host:port)
            account_id: Account identifier for profile isolation
            optimize_bandwidth: Block CSS/fonts to save bandwidth
            load_images: Allow images to load (for manual login visibility)

        Raises:
            ConnectionError: If all retry attempts fail (proxy leak persists)
        """
        last_error = None

        for attempt in range(1, self.MAX_CLIENT_INIT_RETRIES + 1):
            try:
                self.logger.info(
                    f"[Browser Init] Attempt {attempt}/{self.MAX_CLIENT_INIT_RETRIES}: "
                    f"Initializing Client..."
                )

                # Initialize the client
                self.client = Client(
                    headless=headless,
                    enable_mobile_emulation=enable_mobile_emulation,
                    proxy=proxy,
                    account_id=account_id,
                    optimize_bandwidth=optimize_bandwidth,
                    load_images=load_images,
                )

                # If we get here, initialization succeeded (IP validated)
                self.logger.info(
                    f"[Browser Init] ✅ Client initialized successfully on attempt {attempt}"
                )
                return  # Success - exit the method

            except ConnectionError as e:
                # IP Kill Switch triggered - proxy leak detected or validation failed
                last_error = e
                self.logger.warning(
                    f"⚠️ Security Stop triggered (Attempt {attempt}/{self.MAX_CLIENT_INIT_RETRIES}). "
                    f"Reason: {e}"
                )

                # Ensure browser is fully closed before retry
                if self.client is not None:
                    try:
                        self.client.quit()
                    except Exception:
                        pass  # Best effort cleanup
                    finally:
                        self.client = None

                # Check if this was the last attempt
                if attempt >= self.MAX_CLIENT_INIT_RETRIES:
                    self.logger.critical(
                        f"❌ FAILED TO INITIALIZE CLIENT after {self.MAX_CLIENT_INIT_RETRIES} attempts. "
                        f"Last error: {last_error}"
                    )
                    raise  # Re-raise the ConnectionError to stop the process

                # Wait before retry to allow proxy rotation / cleanup
                self.logger.info(f"[Browser Init] Waiting 2 seconds before retry...")
                time.sleep(2)

            except Exception as e:
                # Other unexpected errors - don't retry, just fail
                self.logger.error(
                    f"[Browser Init] Unexpected error during initialization: {e}"
                )
                if self.client is not None:
                    try:
                        self.client.quit()
                    except Exception:
                        pass
                    finally:
                        self.client = None
                raise

    def login(
        self,
        email: str,
        password: Optional[str] = None,
        cookies_file: Optional[str] = None,
        cookies_str: Optional[str] = None,
        use_cookies: bool = False,
        save_cookies: bool = True,
        mobile_emulation: bool = False,
        headless: bool = True,
        proxy: Optional[str] = None,
        account_id: Optional[str] = None,
    ) -> Tuple[Dict, Optional[BytesIO]]:
        """Login to Facebook with Anti-Detect capabilities

        Args:
            email: Facebook email
            password: Facebook password (optional if using cookies)
            cookies_file: Path to cookies file (optional)
            cookies_str: Cookies string (optional)
            use_cookies: Whether to use cookies for login
            mobile_emulation: Whether to use mobile emulation
            proxy: Override proxy string for this session (optional)
            account_id: Override account ID for profile isolation (optional)

        Returns:
            Tuple[Dict, Optional[BytesIO]]: Login result and screenshot
        """
        # Use instance proxy/account_id if not overridden
        effective_proxy = proxy or self._proxy
        effective_account_id = account_id or self._account_id or email

        # Initialize client if not already initialized (with retry logic for IP Kill Switch)
        if self.client is None:
            self._init_client_safe(
                headless=headless,
                enable_mobile_emulation=mobile_emulation,
                proxy=effective_proxy,
                account_id=effective_account_id,
                optimize_bandwidth=self._optimize_bandwidth,
                load_images=self._load_images,
            )

        # Take screenshot for verification
        screenshot = None

        # Try to login
        try:
            # If using cookies
            if use_cookies:
                # Login with cookies from file
                if cookies_file:
                    try:
                        if cookies_file.endswith(".json"):
                            with open(cookies_file, "r") as f:
                                data = json.load(f)
                                cookies = (
                                    data.get("cookies")
                                    if isinstance(data, Dict)
                                    and data.get("cookies", None)
                                    else data
                                )
                        elif cookies_file.endswith(".pkl"):
                            with open(cookies_file, "rb") as f:
                                cookies = pickle.load(f)
                        else:
                            return {
                                "status": "error",
                                "message": "Invalid cookies file format. Must be .json or .pkl",
                                "error_type": "file_format",
                            }, self._take_screenshot()
                        if save_cookies:
                            os.makedirs("cookies", exist_ok=True)
                            cookies_file = os.path.join("cookies", email + ".json")
                            self.client.save_cookies(cookies, cookies_file)
                        result = self.client.login(
                            email=email, use_cookies=True, cookies_file=cookies_file
                        )
                    except Exception as e:
                        return {
                            "status": "error",
                            "message": f"Failed to load cookies: {str(e)}",
                            "error_type": "cookies_error",
                        }, self._take_screenshot()
                # Login with cookies string
                elif cookies_str:
                    try:
                        self.client.get("https://facebook.com")
                        cookies = self.client.load_cookies_from_str(cookies_str, True)
                        # self.client.refresh()
                        sleep_thread = Thread(target=sleep, args=(5,))
                        sleep_thread.start()
                        sleep_thread.join()

                        # Check if login successful
                        if "login" in self.client.current_url:
                            return {
                                "status": "error",
                                "message": "Failed to login with cookies string",
                                "error_type": "cookies_error",
                            }, self._take_screenshot()

                        result = {
                            "status": "ok",
                            "message": "Logged in successfully with cookies string",
                        }

                        if save_cookies:
                            os.makedirs("cookies", exist_ok=True)
                            cookies_file = os.path.join("cookies", email + ".json")
                            self.client.save_cookies(cookies, cookies_file)
                    except Exception as e:
                        return {
                            "status": "error",
                            "message": f"Failed to login with cookies string: {str(e)}",
                            "error_type": "cookies_error",
                        }, self._take_screenshot()
                else:
                    return {
                        "status": "error",
                        "message": "No cookies provided (file or string)",
                        "error_type": "missing_cookies",
                    }, self._take_screenshot()
            # Login with email and password
            else:
                if not password:
                    return {
                        "status": "error",
                        "message": "Password is required for login with credentials",
                        "error_type": "missing_password",
                    }, self._take_screenshot()

                # Login with email and password
                # For login with credentials, we don't use mobile emulation
                if self.client:
                    self.client.quit()
                    self.client = None
                self._init_client_safe(
                    headless=True,
                    enable_mobile_emulation=False,
                    proxy=effective_proxy,
                    account_id=effective_account_id,
                    optimize_bandwidth=self._optimize_bandwidth,
                )

                result = self.client.login(
                    email=email,
                    password=password,
                )

            self.current_account = email

            # Always take screenshot for verification
            screenshot = self._take_screenshot()

            return result, screenshot

        except Exception as e:
            # Handle any exceptions during login
            error_result = {
                "status": "error",
                "message": str(e),
                "error_type": "exception",
            }

            # Try to take screenshot if possible
            try:
                screenshot = self._take_screenshot()
            except:
                pass

            return error_result, screenshot

    def get_cookies(self) -> Optional[dict]:
        """Get cookies from the current session

        Returns:
            Optional[dict]: Cookies if available
        """
        if not self.client:
            return None

        try:
            return self.client.get_cookies()
        except Exception:
            return None

    def save_cookies(self, file_path: str) -> bool:
        """Save cookies to a file

        Args:
            file_path: Path to save cookies to

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.client:
            return False

        try:
            cookies = self.client.get_cookies()

            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Save cookies
            if file_path.endswith(".json"):
                with open(file_path, "w") as f:
                    json.dump(cookies, f)
            elif file_path.endswith(".pkl"):
                with open(file_path, "wb") as f:
                    pickle.dump(cookies, f)
            else:
                # Default to json
                with open(file_path, "w") as f:
                    json.dump(cookies, f)

            return True
        except Exception:
            return False

    def react_post(
        self,
        post_url: str,
        react_type: Literal[
            "Like", "Haha", "Love", "Care", "Wow", "Sad", "Angry"
        ] = "Like",
    ) -> Tuple[Dict, Optional[BytesIO]]:
        """React to a Facebook post

        Args:
            post_url: URL of the post to react to
            react_type: Type of reaction

        Returns:
            Tuple[Dict, BytesIO]: Result and screenshot
        """
        if not self.client:
            return {
                "status": "error",
                "message": "Not logged in",
                "error_type": "not_logged_in",
            }, None

        try:
            # React to post
            result = self.client.react(post_url=post_url, react=react_type)

            # Take screenshot
            screenshot = self._take_screenshot()

            return result, screenshot
        except Exception as e:
            error_result = {
                "status": "error",
                "message": str(e),
                "error_type": "exception",
            }

            # Try to take screenshot if possible
            try:
                screenshot = self._take_screenshot()
            except:
                screenshot = None

            return error_result, screenshot

    def comment_post(
        self,
        post_url: str,
        comment_text: str,
    ) -> Tuple[Dict, Optional[BytesIO]]:
        """Comment on a Facebook post

        Args:
            post_url: URL of the post to comment on
            comment_text: Text of the comment

        Returns:
            Tuple[Dict, BytesIO]: Result and screenshot
        """
        if not self.client:
            return {
                "status": "error",
                "message": "Not logged in",
                "error_type": "not_logged_in",
            }, None

        try:
            # Comment on post
            result = self.client.comment(post_url=post_url, cmnt=comment_text)

            # Take screenshot
            screenshot = self._take_screenshot()

            return result, screenshot
        except Exception as e:
            error_result = {
                "status": "error",
                "message": str(e),
                "error_type": "exception",
            }

            # Try to take screenshot if possible
            try:
                screenshot = self._take_screenshot()
            except:
                screenshot = None

            return error_result, screenshot

    def follow_page(
        self,
        page_url: str,
    ) -> Tuple[Dict, Optional[BytesIO]]:
        """Follow a Facebook page

        Args:
            page_url: URL of the page to follow

        Returns:
            Tuple[Dict, BytesIO]: Result and screenshot
        """
        if not self.client:
            return {
                "status": "error",
                "message": "Not logged in",
                "error_type": "not_logged_in",
            }, None

        try:
            # Follow page
            result = self.client.follow(page_url=page_url)

            # Take screenshot
            screenshot = self._take_screenshot()

            return result, screenshot
        except Exception as e:
            error_result = {
                "status": "error",
                "message": str(e),
                "error_type": "exception",
            }

            # Try to take screenshot if possible
            try:
                screenshot = self._take_screenshot()
            except:
                screenshot = None

            return error_result, screenshot

    def share_post(
        self,
        post_url: str,
        # share_text: str = "",
        # visibility: Literal["public", "friends", "only_me"] = "public",
    ) -> Tuple[Dict, Optional[BytesIO]]:
        """Share a Facebook post

        Args:
            post_url: URL of the post to share
            share_text: Text to add to the share
            visibility: Visibility of the share

        Returns:
            Tuple[Dict, BytesIO]: Result and screenshot
        """
        if not self.client:
            return {
                "status": "error",
                "message": "Not logged in",
                "error_type": "not_logged_in",
            }, None

        try:
            # Share post
            result = self.client.share(
                post_url=post_url,  # share_text=share_text, visibility=visibility
            )

            # Take screenshot
            screenshot = self._take_screenshot()

            return result, screenshot
        except Exception as e:
            error_result = {
                "status": "error",
                "message": str(e),
                "error_type": "exception",
            }

            # Try to take screenshot if possible
            try:
                screenshot = self._take_screenshot()
            except:
                screenshot = None

            return error_result, screenshot

    def check_account(
        self,
        email: str,
        cookies_file: Optional[str] = None,
    ) -> Tuple[Dict, Optional[BytesIO]]:
        """Check if an account's cookies are still valid

        Args:
            email: Facebook email
            cookies_file: Path to cookies file

        Returns:
            Tuple[Dict, Optional[BytesIO]]: Check result and screenshot
        """
        try:
            # Try to login with cookies to check if they're valid
            result, screenshot = self.login(
                email,
                cookies_file=cookies_file,
                use_cookies=True,
                save_cookies=False,  # Don't overwrite existing cookies
                mobile_emulation=False,
            )

            # Close the browser session since we're just checking
            if self.client:
                self.client.quit()
                self.client = None

            return result, screenshot

        except Exception as e:
            error_result = {
                "status": "error",
                "message": str(e),
                "error_type": "exception",
            }

            # Try to take screenshot if possible
            try:
                screenshot = self._take_screenshot()
            except:
                screenshot = None

            # Close browser session if still open
            if self.client:
                self.client.quit()
                self.client = None

            return error_result, screenshot

    def _take_screenshot(self) -> BytesIO:
        """Take a screenshot of the current browser window

        Returns:
            BytesIO: Screenshot image as BytesIO object
        """
        if not self.client:
            raise ValueError("Client not initialized")

        # Take screenshot
        path = "screenshots/" + uuid.uuid1().hex + ".png"
        self.client.save_screenshot(path)

        return path

    def close(self) -> None:
        """Close the Facebook client"""
        if self.client:
            try:
                self.client.close()
            except:
                pass
            finally:
                self.client = None
                self.current_account = None
