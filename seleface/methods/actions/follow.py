from time import sleep
from typing import Dict, Literal

from selenium.webdriver.common.by import By

import seleface


class Follow:
    def follow(
        client: "seleface.Client",
        page_url: str,
    ) -> Dict:
        data = {
            "status": "ok",
            "message": f"Followed successfully!",
            "error_type": None,
        }
        client.get(page_url)
        client.wait.until(
            lambda client: client.execute_script("return document.readyState")
            == "complete"
        )
        client.refresh()
        client.wait.until(
            lambda client: client.execute_script("return document.readyState")
            == "complete"
        )
        sleep(5)
        lang = (
            "en"
            if client.find_element(By.TAG_NAME, "html").get_attribute("lang") == "en"
            else "ar"
        )
        try:
            follow_btn = client.find_element(
                By.XPATH,
                """
                //div[
                contains(@aria-label, 'Follow') or 
                contains(@aria-label, 'متابعة')
                ]
                """,
            )
        except:
            try:
                follow_btn = client.find_element(
                    By.XPATH,
                    """
                    //div[
                    contains(@aria-label, 'Like') or 
                    contains(@aria-label, 'إعجاب بـ')
                    ]
                    """,
                )
            except:
                data["status"] = "error"
                data["message"] = "Follow button not found"
                data["error_type"] = "follow_button_not_found"
                return data
        client.execute_script("arguments[0].click();", follow_btn)
        sleep(1)
        return data
