from time import sleep
from typing import Dict

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import seleface


class Comment:
    def comment(client: "seleface.Client", post_url: str, cmnt: str = "❤") -> Dict:
        """Add Comment To a Post

        Args:
            post_url (str): Post URL
            cmnt (str, optional): Comment. Defaults to "❤".

        Returns:
            Dict: Dictionry of response
        """
        data = {
            "status": "ok",
            "message": f"post was commented successfully!",
            "error_type": None,
        }
        client.get(post_url)
        # client.wait.until(
        #     lambda client: client.execute_script("return document.readyState")
        #     == "complete"
        # )
        sleep(10)
        # input("[+] Press Enter to continue...")
        # open_comment_btn = client.wait.until(
        #     EC.element_to_be_clickable(
        #         (By.XPATH, '//div[@role="button" and contains(@aria-label, "comment")]')
        #     )
        # )
        open_comment_btn = client.find_element(
            By.XPATH, '//div[@role="button" and contains(@aria-label, "comment")]'
        )
        client.execute_script(
            "arguments[0].click();",
            open_comment_btn,
        )
        sleep(0.5)
        commenting_area = client.find_element(By.XPATH, "//textarea[@role='combobox']")
        commenting_area.send_keys(cmnt)
        sleep(0.5)
        comment_btn = client.find_element(
            By.XPATH,
            """
            //div[
                contains(@aria-label, 'نشر تعليق') or 
                contains(@aria-label, 'Post a comment')
            ]
            """,
        )
        client.execute_script("arguments[0].click();", comment_btn)
        sleep(3)
        return data
