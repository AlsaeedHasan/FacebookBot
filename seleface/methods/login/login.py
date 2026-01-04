import os
from time import sleep
from typing import Dict

from selenium.webdriver.common.by import By

import seleface
from seleface.logger import Logger
from seleface.methods.login.cookies import Cookies
from seleface.utils.helpers import read


class Login(Cookies):
    # Get a logger instance for the login module
    logger = Logger.get_logger("seleface.login")

    def login(
        client: "seleface.Client",
        email: str,
        password: str = None,
        cookies_file: os.PathLike | str = None,
        use_cookies: bool = False,
    ) -> Dict:
        """Login into an account using both email and password or cookies

        Args:
            email (str): Account email
            password (str, optional): Account password. Defaults to None.
            cookies_file (os.PathLike | str, optional): Local Cookies file. Defaults to None.
            use_cookies (bool, optional): True If You Want To Use Cookie File. Defaults to False.
            save_login (bool, optional): True If You Want To Save Cookies File. Defaults to False.

        Returns:
            Dict: Dictionry of response
        """
        on_success_return = {
            "status": "ok",
            "message": "logged in successfully",
            "error_type": None,
        }
        Login.logger.info(
            f"Attempting to login with email: {email} {'using cookies' if use_cookies else 'using credentials'}"
        )
        client.get("http://facebook.com")
        Login.logger.debug("Navigated to Facebook login page")
        client.wait.until(
            lambda client: client.execute_script("return document.readyState")
            == "complete"
        )
        if use_cookies:
            Login.logger.debug(
                f"Reading cookies from {cookies_file or f'./cookies/{email}.json'}"
            )
            cookies = read(cookies_file or f"./cookies/{email}.json")
            client.delete_all_cookies()
            client.load_cookies(cookies)
            client.refresh()
            client.wait.until(
                lambda client: client.execute_script("return document.readyState")
                == "complete"
            )
            Login.logger.info("Successfully logged in using cookies")
            return on_success_return
        else:
            email_input = client.find_element(By.NAME, "email")
            password_input = client.find_element(By.NAME, "pass")
            submit = client.find_element(By.XPATH, "//button[@name='login']")
            Login.logger.debug("Filling login form")
            email_input.send_keys(email)
            password_input.send_keys(password)
            client.execute_script("arguments[0].click();", submit)
            Login.logger.debug("Submitted login form, waiting for page to load")
            sleep(10)
            client.wait.until(
                lambda client: client.execute_script("return document.readyState")
                == "complete"
            )
            sleep(5)
            lang = (
                "en"
                if client.find_element(By.TAG_NAME, "html").get_attribute("lang")
                == "en"
                else "ar"
            )
            check_text = "Remember Password" if lang == "en" else "تذكر كلمة السر"
            ok_button_text = "OK" if lang == "en" else "موافق"
            if "The password that you've entered is incorrect" in client.page_source:
                Login.logger.warning(f"Login failed for {email}: Incorrect password")
                return {
                    "status": "bad",
                    "message": "incorrect password",
                    "error_type": "credintials",
                }
            elif "login" in client.current_url:
                Login.logger.warning(
                    f"Login failed for {email}: Still on login page, check credentials"
                )
                return {
                    "status": "bad",
                    "message": "Please, check your email and password",
                    "error_type": "unknown",
                }
            elif (
                not all(
                    [
                        "verification" in client.current_url,
                        "checkpoint" in client.current_url,
                        client.page_source
                        not in [
                            "https://m.facebook.com/",
                            "https://wwww.facebook.com/",
                        ],
                    ]
                )
                or check_text in client.page_source
            ):
                Login.logger.info(f"Login successful for {email}")
                if not os.path.exists("cookies"):
                    Login.logger.debug("Creating cookies directory")
                    os.mkdir("cookies")
                if check_text in client.page_source:
                    submit_save_info_button = client.find_element(
                        By.XPATH, f"//div[@aria-label='{ok_button_text}']"
                    )
                    client.execute_script(
                        "arguments[0].click();", submit_save_info_button
                    )
                    sleep(5)
                cookies = client.get_cookies()
                cookie_path = cookies_file or ("cookies/" + email + ".json")
                Login.logger.debug(f"Saving cookies to {cookie_path}")
                client.save_cookies(cookies, cookie_path)
                on_success_return["message"] += " (login saved)"
                Login.logger.info(f"Login successful and cookies saved for {email}")
                return on_success_return
            else:
                Login.logger.error(f"Login failed for {email}: Unexpected state")
                return {
                    "status": "bad",
                    "message": "not expected",
                    "error_type": "unknown",
                }
