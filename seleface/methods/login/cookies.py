import os
from typing import Dict, List, Optional, Union

from selenium import webdriver

from seleface.utils.helpers import read, write


class Cookies:
    """
    A utility class for managing cookies with Selenium WebDriver.

    This class provides methods to load cookies into a WebDriver instance and save cookies
    to a JSON file. It simplifies the process of maintaining session data for web automation.
    Also provides methods for login using cookies provided as a string or JSON file.
    """

    def load_cookies(
        driver: webdriver.Chrome, cookies: List[Dict], url="https://facebook.com"
    ):
        """
        Load cookies into a Selenium WebDriver instance.

        :param cookies: List of cookies (as dictionaries) to be loaded into the WebDriver.
        :param url: The URL of the domain where cookies should be loaded.
                    Defaults to "https://facebook.com". If None, the domain will be inferred from the cookies.
        """
        if url:
            driver.get(url)
        else:
            domain = cookies[0]["domain"]
            driver.get(f"http://{domain}")
        for cookie in cookies:
            driver.add_cookie({"name": cookie["name"], "value": cookie["value"]})

    def load_cookies_from_str(
        driver: webdriver.Chrome,
        cookies: str,
        url="https://facebook.com",
        return_cookies=False,
    ):
        """
        Load cookies into a Selenium WebDriver instance.

        :param cookies: str of cookies to be loaded into the WebDriver.
        :param url: The URL of the domain where cookies should be loaded.
        """
        driver.get(url)
        cookies = [
            {"name": item.split("=")[0], "value": item.split("=")[1]}
            for item in cookies.split(";")[:-1]
        ]
        for cookie in cookies:
            driver.add_cookie(cookie)
        if return_cookies:
            return cookies

    @staticmethod
    def cookies_to_str(cookies: Dict) -> str:
        """
        Convert cookies to str.

        :param cookies: A list of cookies (as dictionaries) to be convert.
        """
        str_cookies = ";".join(
            [f"{cookie['name']}={cookie['value']}" for cookie in cookies]
        )
        return str_cookies

    @staticmethod
    def str_to_dict(cookies: str) -> Dict:
        """
        Convert str cookies to dict.

        :param cookies: A str of cookies to be convert.
        """
        cookies = [
            {"name": item.split("=")[0], "value": item.split("=")[1]}
            for item in cookies.split(";")[:-1]
        ]
        return cookies

    @staticmethod
    def save_cookies(cookies, file_path="./cookies.json"):
        """
        Save cookies to a JSON file.

        :param cookies: A list of cookies (as dictionaries) to be saved.
        :param file_path: The file path where the cookies will be saved as a JSON file.
                          Defaults to "cookies.json".
        """
        # cookies = [
        #     {"name": cookie["name"], "value": cookie["value"]} for cookie in cookies
        # ]
        write(cookies, file_path)

    @staticmethod
    def read_cookies_file(cookies_file: str) -> Dict:
        """
        Read cookies from a JSON file.

        :param cookies_file: The file path where the cookies will saved as a JSON file.
        """
        cookies = read(cookies_file)
        return cookies

    @staticmethod
    def login_with_cookies(
        driver: webdriver.Chrome,
        cookies_data: Union[str, Dict, List[Dict]],
        url: str = "https://facebook.com",
    ) -> Dict:
        """
        Login to Facebook using cookies provided as a string, dictionary, or list of dictionaries.

        :param driver: The Selenium WebDriver instance.
        :param cookies_data: Cookies data as a string, dictionary, or list of dictionaries.
        :param url: The URL to navigate to after loading cookies.
        :return: Dictionary containing login status and message.
        """
        result = {"success": False, "message": "", "screenshot_path": None}

        try:
            # Handle different cookie formats
            if isinstance(cookies_data, str):
                # Check if it's a file path
                if os.path.exists(cookies_data) and cookies_data.endswith(".json"):
                    cookies = Cookies.read_cookies_file(cookies_data)
                    Cookies.load_cookies(driver, cookies, url)
                else:
                    # Assume it's a cookie string
                    Cookies.load_cookies_from_str(driver, cookies_data, url)
            elif isinstance(cookies_data, dict) or isinstance(cookies_data, list):
                Cookies.load_cookies(driver, cookies_data, url)
            else:
                result["message"] = "Invalid cookies format"
                return result

            # Refresh the page to apply cookies
            driver.refresh()

            # Check if login was successful
            if (
                "login" not in driver.current_url
                and "checkpoint" not in driver.current_url
            ):
                result["success"] = True
                result["message"] = "Successfully logged in using cookies"
            else:
                result["message"] = "Failed to login with cookies"

        except Exception as e:
            result["message"] = f"Error logging in with cookies: {str(e)}"

        return result

    @staticmethod
    def verify_login_with_screenshot(
        driver: webdriver.Chrome, screenshot_path: Optional[str] = None
    ) -> Dict:
        """
        Take a screenshot of the current page to verify login status.

        :param driver: The Selenium WebDriver instance.
        :param screenshot_path: Path to save the screenshot. If None, a default path will be used.
        :return: Dictionary containing verification status and screenshot path.
        """
        result = {
            "success": False,
            "screenshot_path": screenshot_path or "./facebook_login_verification.png",
        }

        try:
            # Take screenshot
            driver.save_screenshot(result["screenshot_path"])
            result["success"] = True
        except Exception as e:
            result["message"] = f"Error taking screenshot: {str(e)}"

        return result
