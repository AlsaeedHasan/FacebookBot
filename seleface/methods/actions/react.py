from time import sleep
from typing import Dict, Literal

from selenium.webdriver.common.by import By

import seleface


class React:
    def react(
        client: "seleface.Client",
        post_url: str,
        react: Literal["Like", "Haha", "Love", "Care", "Wow", "Sad", "Angry"] = "Like",
    ) -> Dict:
        """Like a post

        Args:
            post_url (str): Post URL

        Returns:
            Dict: Dictionry of response
        """
        data = {
            "status": "ok",
            "message": f"{react} was done successfully!",
            "error_type": None,
        }
        client.get(post_url)
        client.wait.until(
            lambda client: client.execute_script("return document.readyState")
            == "complete"
        )
        sleep(5)
        # input("[DEBUG] Press Enter after the post is fully loaded...")
        like_btn = client.find_element(By.XPATH, '//div[contains(@aria-label, "like")]')
        client.execute_script("arguments[0].click();", like_btn)
        sleep(1)
        # post_element = get_post_element(client, post_url)
        # if post_element:
        # with open("elem.png", "wb") as f:
        #     f.write(post_element.screenshot_as_png)
        # sleep(1)
        # show_react_btn = post_element.find_element(
        #     By.XPATH, "//div[@aria-label='React']"
        # )
        # client.execute_script("arguments[0].click();", show_react_btn)
        # reactions_bar = client.find_element(
        #     By.XPATH, "//div[@aria-label='Reactions']"
        # )
        # react_btn = reactions_bar.find_elements(
        #     By.XPATH, f"//div[@aria-label='{react}']"
        # )[-1]
        # like_btn = post_element.find_element(
        #     By.XPATH, "//div[@aria-label='Like']"
        # )
        # like_btn.click()
        # if react == "Like":
        #     sleep(1)
        # else:
        #     data["status"] = "bad"
        #     data["message"] = "can only react with Like for now"
        #     data["error_type"] = "element_not_found"
        # action = ActionChains(client)
        # action.move_to_element(like_element).perform()
        # sleep(1)
        # action.move_to_element(react_element).perform()
        # client.execute_script("arguments[0].click();", react_element)
        # sleep(1)
        # else:
        #     data["status"] = "bad"
        #     data["message"] = "can not find post area"
        #     data["error_type"] = "element_not_found"
        return data
