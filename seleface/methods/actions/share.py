from time import sleep
from typing import Dict, Literal, Optional

from selenium.webdriver.common.by import By

import seleface
from seleface.logger import Logger

# Configure logger
logger = Logger.get_logger("share_action")


class Share:
    def share(
        client: "seleface.Client",
        post_url: str,
        # share_text: str = "",
        # visibility: Literal["public", "friends", "only_me"] = "public"
    ) -> Dict:
        """Share a Facebook post

        Args:
            client: Logged in seleface client
            post_url: URL of the post to share
            share_text: Optional text to add with the share
            visibility: Visibility of the share (public, friends, only_me)

        Returns:
            Dict containing operation status and error info if any
        """
        data = {
            "status": "ok",
            "message": f"Shared successfully!",
            "error_type": None,
            "success": False,
            "error_info": None,
            "screenshot_path": None,
        }
        client.get(post_url)
        client.wait.until(
            lambda client: client.execute_script("return document.readyState")
            == "complete"
        )
        # client.refresh()
        # client.wait.until(
        #     lambda client: client.execute_script("return document.readyState")
        #     == "complete"
        # )
        sleep(5)
        lang = (
            "en"
            if client.find_element(By.TAG_NAME, "html").get_attribute("lang") == "en"
            else "ar"
        )
        share_btn = client.find_element(
            By.XPATH, '//div[contains(@aria-label, "share")]'
        )
        client.execute_script("arguments[0].click();", share_btn)
        sleep(3)
        facebook_share = client.find_element(
            By.XPATH,
            """
            //div[
            contains(@aria-label, 'Share to Facebook') or 
            contains(@aria-label, 'مشاركة على فيسبوك')
            ]
            """,
        )
        client.execute_script("arguments[0].click();", facebook_share)
        sleep(5)
        submit_btn = client.find_element(
            By.XPATH,
            """
            //div[
            contains(@aria-label, 'Post') or 
            contains(@aria-label, 'نشر')
            ]
            """,
        )
        client.execute_script("arguments[0].click();", submit_btn)
        sleep(5)
        return data
