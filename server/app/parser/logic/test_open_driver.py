import time
# import atexit # Removed atexit

from server.app.GLOBAL import GLOBAL
from server.app.parser.driver.driver import BaseSeleniumDriver
# from server.app.parser.proxy import Proxy # Proxy import removed

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

def open_driver():
    # global _driver_instance # REMOVED
    new_driver = None
    try:
        # Create proxy object with your provided credentials - REMOVED FOR DEBUGGING
        # proxy = Proxy(
        #     host="51.79.24.25",
        #     port=5959,
        #     username="pcpMAoasQU-res-us-sid-53455046",
        #     userpass="PC_2ZlzEvfqfUB6w4cvv"
        # )

        # Create driver (without explicit proxy for debugging)
        new_driver = BaseSeleniumDriver(
            executable_path=GLOBAL.PATH.CHROMEDRIVER_PATH,
            # proxy=proxy, # Proxy argument removed, will use EmptyProxy by default
            headless=False,
            window_size=(400, 700)
        )
        # _driver_instance = new_driver # REMOVED

        print("Creating driver instance...")
        new_driver.create_instance()
        
        print("Navigating to mobile.de...")
        new_driver.get("https://mobile.de/")

        print("Waiting for 30 seconds...")
        time.sleep(30)
        print("Checking IP address...")
        new_driver.get("https://api.ipify.org")
        ip = new_driver.find_element("tag name", "pre").text
        print(f"Current IP address: {ip}")
        
        print("Waiting for 30 seconds...")
        time.sleep(30)
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
    finally:
        if new_driver:
            print("Quitting driver (from finally block in open_driver)...")
            try:
                new_driver.quit()
                print("Driver quit successfully (from finally block).")
            except Exception as e:
                print(f"Error while quitting driver (from finally block): {str(e)}")

if __name__ == "__main__":
    # atexit.register(cleanup_driver, _driver_instance) # REMOVED - _driver_instance would be None here anyway
    # It's better to register atexit with the actual instance if used, but here we rely on finally
    
    try:
        open_driver()
    except KeyboardInterrupt:
        print("\nScript interrupted by user.")
        # The finally block in open_driver should still execute if new_driver was assigned
    except Exception as e:
        print(f"Unexpected error in main: {str(e)}")
    finally:
        print("Script finished.")

