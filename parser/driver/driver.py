import re
import time
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import selenium.common.exceptions
from filelock import FileLock
import os

import logging

from proxy import ProxyABC, Proxy, EmptyProxy
from proxy.connector import ProxyConnectorExtension
from utils.bot.scrollers import VerticalScroller
from utils.selenium import driver_processes
from ..exceptions.driver import TryAgainPageError, BrowserClosedError

class BaseSeleniumDriver(uc.Chrome):
    """
    Connects to chrome executable as debugger to control it.
    Has methods for effective control chrome for parsing tweeter.
    """

    def __init__(
            self,
            executable_path: str,
            proxy: ProxyABC = EmptyProxy,  # here is can be EmptyProxy or valid Proxy
            user_agent: str = '',
            headless=True,
            window_size=(400, 700),
            logger=None,
    ):
        self.executable_path = executable_path
        self.proxy = proxy
        self.user_agent = user_agent
        self.headless = headless
        self.window_size = window_size
        self.logger = logger or logging.getLogger(__name__)

        self.vertical_scroller = VerticalScroller(self)
        self.instance_exist = False
        self.service = None # Initialize service attribute

    def create_instance(self):
        try:
            self.__create_instance()
        except selenium.common.exceptions.WebDriverException as error:
            if 'supports chrome version' in str(error).lower():
                versions_msg_part = str(error)[str(error).lower().find('supports chrome version'):]
                versions = [match.group() for match in re.finditer(r'[\d.]+', versions_msg_part)]
                if len(versions) > 1:
                    supports_version, current_version = versions[:2]
                    raise TryAgainPageError(f"Your Chrome version is: {current_version}<br>"
                                            f"Please install Chrome {supports_version} for stable operation.")
                else:
                    raise TryAgainPageError("An error has occurred, likely related to your Chrome version.")
        except TypeError as error:
            if 'binary location must be a string' in str(error).lower():
                raise TryAgainPageError("Failed to find Chrome on your PC. Please install Chrome.")

    def __create_instance(self):
        # 1. Check if instance exists
        if self.instance_exist:
            return self.logger.warning("Instance already exists")

        # 2. Create lock file path in user's home directory
        lock_path = os.path.join(os.path.expanduser('~'), '.chromedriver.lock')
        lock = FileLock(lock_path)

        try:
            lock.acquire(timeout=30)

            try:
                options = uc.ChromeOptions()

                # Basic required options
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-gpu')

                # Set user agent before other automation-related options
                if self.user_agent and self.user_agent.strip():
                    options.add_argument(f'--user-agent={self.user_agent}')
                    self.logger.info(f"Setting user agent: {self.user_agent}")

                # Add other options after user agent
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--disable-popup-blocking')
                options.add_argument('--profile-directory=Default')
                options.add_argument('--disable-blink-features=BlockCredentialedSubresources')
                options.add_argument('--disable-infobars')
                options.add_argument("--disable-media")
                options.add_argument("--mute-audio")
                options.add_argument("--lang=en")

                if self.headless:
                    options.add_argument('--headless')

                if isinstance(self.proxy, Proxy):
                    proxy_connector = ProxyConnectorExtension(self.proxy)
                    options.add_argument(f'--load-extension={proxy_connector.get_extension_dir()}')
                    # Universal proxy argument that works for both types
                    options.add_argument(f'--proxy-server=http://{self.proxy.host}:{self.proxy.port}')
                else:
                    print("No proxy provided ")
                    print(f"type(self.proxy): {type(self.proxy)}")
                    print(f"Proxy: {Proxy}")
                    print(f"self.proxy.__class__ == Proxy: {self.proxy.__class__ == Proxy}")
                    print(f"isinstance(self.proxy, Proxy): {isinstance(self.proxy, Proxy)}")

                    

                # Store the service object on the instance
                self.service = Service(self.executable_path)

                super().__init__(
                    options=options,
                    service=self.service, # Pass the stored service
                )

                # Verify user agent after initialization
                try:
                    actual_user_agent = self.execute_script("return navigator.userAgent;")
                    self.logger.info(f"Actual user agent being used: {actual_user_agent}")
                except Exception as e:
                    self.logger.error(f"Could not verify user agent: {e}")

                self.set_page_load_timeout(60)
                self.set_window_size(*self.window_size)
                self.instance_exist = True

                # hide undetected_chromedriver`s console window
                driver_processes.hide_drivers_command_prompt()
            except Exception as e:
                self.logger.error(f"Error during driver initialization: {e}", exc_info=True)
                raise
        except TimeoutError:
            self.logger.error("Timeout waiting for lock")
            raise
        except Exception as e:
            self.logger.error(f"Error during driver initialization: {e}", exc_info=True)
            raise
        finally:
            if lock.is_locked:
                lock.release()

    def get(self, url: str):
        """
        Gets page with passing "Try again" page.

        Raises:
             - TryAgainPageError when can't pass "Try Again" Twitter page.
        """
        self.logger.info(f'Selenium get page: {url}')
        super().get(url)
        # The "Try again" logic might be specific to Twitter and not general.
        # For a general BaseSeleniumDriver, this might need to be optional or removed.
        # If this is for a general ipify.org check, this part is not relevant.
        # try:
        #     for _ in range(10):
        #         WebDriverWait(self, 7).until(
        #             EC.visibility_of_element_located((By.XPATH, '//span[text()="Try again"]'))
        #         )
        #         self.refresh()
        #     raise TryAgainPageError("There were 10 unsuccessful attempts to pass through the 'Try Again' page, "
        #                             "unable to reach the final page.")
        # except selenium.common.exceptions.TimeoutException:
        #     pass # This means "Try again" was not found, which is expected for most sites.
        # except Exception as e:
        #     self.logger.warning(f"Unexpected error during 'Try again' check: {e}")
        #     pass

    def quit(self):
        self.logger.info(f'BaseSeleniumDriver: quit() called. Current instance_exist: {self.instance_exist}')

        if not self.instance_exist:
            self.logger.warning("BaseSeleniumDriver: quit() called, but instance_exist was already False.")
            if hasattr(self, 'service') and self.service: # Check if self.service was initialized
                service_process = getattr(self.service, 'process', None)
                if service_process and service_process.poll() is None:
                    self.logger.info("BaseSeleniumDriver: Lingering service process found. Attempting to stop it.")
                    try:
                        self.service.stop()
                        self.logger.info("BaseSeleniumDriver: Lingering service stopped successfully.")
                    except Exception as e_stop:
                        self.logger.error(f"BaseSeleniumDriver: Error stopping lingering service: {e_stop}", exc_info=True)
                else:
                    self.logger.info("BaseSeleniumDriver: Lingering service process not found or already stopped.")
                self.service = None 
            self.logger.info('BaseSeleniumDriver: quit() finished for already non-existent instance.')
            return

        self.instance_exist = False

        try:
            self.logger.info("BaseSeleniumDriver: Attempting to call super().quit() to close browser and stop service.")
            super().quit()
            self.logger.info("BaseSeleniumDriver: super().quit() completed successfully.")
        except Exception as e:
            self.logger.error(f"BaseSeleniumDriver: Exception during super().quit(): {e}", exc_info=True)
            self.logger.warning("BaseSeleniumDriver: super().quit() failed. Attempting to stop service as a fallback.")
            if hasattr(self, 'service') and self.service:
                service_process = getattr(self.service, 'process', None)
                if service_process and service_process.poll() is None: 
                    self.logger.info("BaseSeleniumDriver: Fallback: Service process appears to be running. Attempting to stop it.")
                    try:
                        self.service.stop()
                        self.logger.info("BaseSeleniumDriver: Fallback: Service stopped successfully.")
                    except Exception as e_stop:
                        self.logger.error(f"BaseSeleniumDriver: Fallback: Error stopping service: {e_stop}", exc_info=True)
                else:
                    self.logger.info("BaseSeleniumDriver: Fallback: Service process not found or already stopped.")
        finally:
            if hasattr(self, 'service'): # Ensure self.service was initialized
                self.service = None
            self.logger.info('BaseSeleniumDriver: quit() method finished execution.')

    def wait_for_window(self, timeout=30):
        """
        Waits for the browser window to remain open for a certain period.
        Raises a BrowserClosedError if the window is closed unexpectedly.
        """
        if not self.instance_exist: # Don't try to wait if instance is already marked as closed
            self.logger.warning("wait_for_window called on a non-existent or closed instance.")
            return
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if not self.window_handles: # This can throw NoSuchWindowException if browser is gone
                    raise BrowserClosedError("The browser window was closed unexpectedly (no window handles).")
                time.sleep(1)
            except selenium.common.exceptions.NoSuchWindowException:
                 self.logger.warning("Window closed while waiting (NoSuchWindowException).")
                 self.instance_exist = False # Mark instance as gone
                 raise BrowserClosedError("The browser window was closed unexpectedly during wait (NoSuchWindowException).")
            except Exception as e: # Catch other potential errors like InvalidSessionIdException
                self.logger.error(f"Error while checking if the window is open: {e}", exc_info=True)
                self.instance_exist = False # Mark instance as gone
                raise BrowserClosedError(f"Error checking window status: {e}")
        self.logger.info("wait_for_window: Window remained open for the specified timeout.")