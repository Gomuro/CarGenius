import time
# import atexit # Removed atexit

from server.app.GLOBAL import GLOBAL
from server.app.parser.driver.driver import BaseSeleniumDriver
from server.app.parser.proxy import ProxyABC, Proxy, EmptyProxy  # Proxy import removed
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global driver variable for cleanup - REMOVED
# _driver_instance = None

# def cleanup_driver(driver_instance):
#     if driver_instance:
#         print("atexit: Cleaning up driver...")
#         try:
#             driver_instance.quit()
#             print("atexit: Driver quit successfully.")
#         except Exception as e:
#             print(f"atexit: Error while quitting driver: {str(e)}")
#         finally:
#             print("atexit: Cleanup finished.")

def logic_mobilede(PROXY: ProxyABC = EmptyProxy()):
    driver = None
    try:
        # Validate proxy
        if isinstance(PROXY, EmptyProxy):
            proxy = EmptyProxy()
            logger.info("No proxy provided, using direct connection")
        else:
            proxy = PROXY
            logger.info(f"Using proxy: {proxy.host}:{proxy.port}")

        # Create driver with validated proxy
        driver = BaseSeleniumDriver(
            executable_path=GLOBAL.PATH.CHROMEDRIVER_PATH,
            proxy=proxy,
            headless=False,
            window_size=(400, 700),
            logger=logger
        )
        # _driver_instance = new_driver # REMOVED

        print("Creating driver instance...")
        driver.create_instance()
        
        # Verify proxy is working
        print("Verifying proxy connection...")
        driver.get("https://api.ipify.org")
        time.sleep(5)
        try:
            ip = driver.find_element(By.TAG_NAME, "pre").text
            print(f"Current IP address: {ip}")
            if isinstance(proxy, Proxy) and ip != proxy.host:
                print(f"Warning: Expected proxy IP {proxy.host} but got {ip}")
        except Exception as e:
            print(f"Error checking IP: {str(e)}")
            raise

        print("Navigating to mobile.de...")
        driver.get("https://mobile.de/")

        print("Waiting for page to load...")
        try:
            # Wait for page to load
            # WebDriverWait(driver, 30).until(
            #     EC.presence_of_element_located((By.TAG_NAME, "body"))
            # )
            time.sleep(10)
            print("Page loaded successfully.")
            
            # Get page source
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            print(soup.prettify())
        except Exception as e:
            print(f"Error waiting for page load: {str(e)}")
            raise

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise
    finally:
        if driver:
            print("Quitting driver (from finally block in open_driver)...")
            try:
                driver.quit()
                print("Driver quit successfully (from finally block).")
            except Exception as e:
                print(f"Error while quitting driver (from finally block): {str(e)}")



