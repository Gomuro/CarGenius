from src.GLOBAL import GLOBAL
from src.driver.user_agent_test_driver import UserAgentTestDriver
import logging

def test_user_agent():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Test user agent
    test_user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    
    try:
        # Create driver instance
        driver = UserAgentTestDriver(
            executable_path=GLOBAL.PATH.CHROMEDRIVER_PATH,
            user_agent=test_user_agent,
            headless=False,  # Set to True if you want to run headless
            logger=logger
        )

        # Verify the user agent
        result = driver.verify_user_agent()
        
        # Print results
        logger.info("User Agent Test Results:")
        logger.info(f"Intended User-Agent: {result['intended_user_agent']}")
        logger.info(f"Actual User-Agent: {result['actual_user_agent']}")
        logger.info(f"Match: {result['matches']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    test_user_agent() 