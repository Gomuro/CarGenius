import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
import logging
import time

class UserAgentTestDriver(uc.Chrome):
    def __init__(
            self,
            executable_path: str,
            user_agent: str,
            headless=False,  # Default to non-headless for testing
            window_size=(800, 600),
            logger=None,
    ):
        self.executable_path = executable_path
        self.user_agent = user_agent
        self.headless = headless
        self.window_size = window_size
        self.logger = logger or logging.getLogger(__name__)
        self.instance_exist = False
        self.actual_user_agent = None
        self._create_instance()

    def _create_instance(self):
        if self.instance_exist:
            return

        options = uc.ChromeOptions()
        
        # Basic required options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        
        # Set user agent before other automation-related options
        if self.user_agent:
            options.add_argument(f'--user-agent={self.user_agent}')
        
        # Add other options after user agent
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("--disable-extensions")
        
        if self.headless:
            options.add_argument('--headless')

        service = Service(self.executable_path)

        # Initialize the Chrome driver
        super().__init__(
            options=options,
            service=service,
        )

        self.set_window_size(*self.window_size)
        self.instance_exist = True

    def verify_user_agent(self):
        """
        Verifies the actual user agent being used by visiting test pages
        and checking through multiple methods.
        """
        try:
            # Method 1: Check through JavaScript
            self.get('https://www.whatismybrowser.com/')
            time.sleep(5)  # Wait for page to load completely
            
            js_user_agent = self.execute_script("return navigator.userAgent;")
            self.logger.info(f"JavaScript User-Agent: {js_user_agent}")
            
            # Method 2: Check through a dedicated user agent service
            self.get('https://www.whatismyua.info/')
            time.sleep(5)  # Wait for page to load completely
            
            # Method 3: Compare with what we set
            self.logger.info(f"Intended User-Agent: {self.user_agent}")
            
            # Store the actual user agent
            self.actual_user_agent = js_user_agent
            
            return {
                'intended_user_agent': self.user_agent,
                'actual_user_agent': js_user_agent,
                'matches': self.user_agent == js_user_agent
            }
            
        except Exception as e:
            self.logger.error(f"Error during user agent verification: {e}")
            raise

    def quit(self):
        """Properly close the driver"""
        if self.instance_exist:
            super().quit()
            self.instance_exist = False 