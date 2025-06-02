import time
import random
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from undetected_chromedriver import WebElement


logger = logging.getLogger(__name__)

def simulate_input_in_element(element_input: WebElement, text, speed_texting_index=3):
    logger.info('Input text')
    try:
        element_input.clear()
    except Exception as e:
        logger.debug(f"Failed to clear element: {e}")
    for char in text:
        try:
            element_input.send_keys(char)
            time.sleep(float(f'0.{speed_texting_index}') + random.uniform(0.1, 0.3))
        except Exception as e:
            logger.debug(f"Failed to send keys: {e}")


def random_sleep(minimum=1, maximum=2):
    time.sleep(random.uniform(minimum, maximum))
