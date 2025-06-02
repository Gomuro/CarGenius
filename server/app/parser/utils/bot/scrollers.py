from undetected_chromedriver import Chrome

import logging

logger = logging.getLogger(__name__)


class VerticalScroller:
    def __init__(self, driver: Chrome):
        self.driver = driver

    @property
    def current_scroll_y(self):
        logger.info('Scroll y')
        resp = self.driver.execute_script('return window.pageYOffset;')
        try:
            current_scroll_y = int(resp)
        except (ValueError, TypeError):
            logger.debug(f'Failed to get new current scroll: {resp}')
            current_scroll_y = 0

        return current_scroll_y

    @property
    def max_scroll_y(self):
        logger.info('Max scroll y')
        resp = self.driver.execute_script("""
            return Math.max( document.body.scrollHeight, document.body.offsetHeight, 
                       document.documentElement.clientHeight, document.documentElement.scrollHeight, 
                       document.documentElement.offsetHeight);
            """)
        try:
            max_scroll_y = int(resp)
        except (ValueError, TypeError):
            logger.debug(f'Failed to get max scroll y: {resp}')
            max_scroll_y = 0

        return max_scroll_y

    def scroll_to(self, y: int):
        logger.info(f'Scroll y to {y}')
        self.driver.execute_script(f'window.scrollTo(0, {y})')
