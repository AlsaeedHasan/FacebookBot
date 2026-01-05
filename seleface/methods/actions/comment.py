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
        client.wait.until(
            lambda client: client.execute_script("return document.readyState")
            == "complete"
        )
        # sleep(10)
        # input("[+] Press Enter to continue...")
        # 2. ننتظر ظهور أي زرار فيه كلمة comment (سواء اللي عايزينه أو لا)
        client.wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, '//div[@role="button" and contains(@aria-label, "comment")]')
            )
        )

        # 3. نجيب كل الزراير المحتملة
        candidates = client.find_elements(
            By.XPATH, '//div[@role="button" and contains(@aria-label, "comment")]'
        )

        target_btn = None

        for btn in candidates:
            label = btn.get_attribute("aria-label")
            if label and len(label) < 25:
                target_btn = btn
                break

        if not target_btn and candidates:
            target_btn = candidates[0]

        if target_btn:
            client.execute_script("arguments[0].click();", target_btn)
        else:
            data["status"] = "error"
            data["message"] = "Comment button not found"
            return data

        sleep(1)

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
        sleep(7)
        return data
