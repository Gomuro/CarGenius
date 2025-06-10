import json
import time
import threading
from datetime import datetime
# import atexit # Removed atexit

from server.app.GLOBAL import GLOBAL
from parser.driver.driver import BaseSeleniumDriver
from proxy import (ProxyABC, Proxy, EmptyProxy)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import logging
from fake_useragent import UserAgent
from parser.exceptions.driver import AccessDeniedError, NoProxyProvidedError  # Add at top
from parser.validator import CarDataValidator  # Add validator import

# Set up logging with a more readable format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
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

def log_section(title):
    """Helper function to create section headers in logs"""
    logger.info(f"\n{'='*50}\n{title}\n{'='*50}")

class AccessDeniedMonitor:
    """Background monitor that checks for access denied every 5 seconds"""
    
    def __init__(self, driver):
        self.driver = driver
        self.monitoring = False
        self.thread = None
        self.access_denied_detected = False
        self.ref_number = None
        self.detection_location = None
        
    def start_monitoring(self):
        """Start background monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.access_denied_detected = False
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            logger.info("🛡️ Started background access denied monitoring (every 5 seconds)")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        logger.info("🛡️ Stopped background access denied monitoring")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                # Check for access denied
                is_blocked, ref_number = check_access_denied(self.driver)
                if is_blocked:
                    self.access_denied_detected = True
                    self.ref_number = ref_number
                    self.detection_location = f"Background monitor at {time.strftime('%H:%M:%S')}"
                    logger.error(f"🚨 BACKGROUND MONITOR: Access denied detected!")
                    logger.error(f"   Time: {time.strftime('%H:%M:%S')}")
                    logger.error(f"   Reference: {ref_number}")
                    logger.error(f"   URL: {self.driver.current_url}")
                    self.monitoring = False  # Stop monitoring
                    break
                    
                # Wait 5 seconds before next check
                time.sleep(5)
                
            except Exception as e:
                # If driver is closed or there's an error, stop monitoring
                logger.debug(f"Background monitor error (likely normal): {str(e)}")
                break
    
    def is_access_denied(self):
        """Check if access denied was detected by background monitor"""
        return self.access_denied_detected
    
    def get_detection_info(self):
        """Get information about access denied detection"""
        return {
            'detected': self.access_denied_detected,
            'ref_number': self.ref_number,
            'location': self.detection_location
        }

def wait_and_find_clickable_element(driver, by, selector, timeout=10, scroll_into_view=True):
    """
    Helper function to wait for an element to be present, visible, and clickable
    Works better in both headless and windowed modes
    """
    try:
        # First wait for element to be present
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
        
        if scroll_into_view:
            # Scroll element into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(1)
        
        # Wait for element to be clickable
        clickable_element = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(element)
        )
        
        return clickable_element
        
    except Exception as e:
        logger.debug(f"Failed to find clickable element {selector}: {str(e)}")
        return None

def check_timeout_error(driver):
    """
    Check if the page shows a timeout/connection error
    """
    try:
        page_source = driver.page_source.lower()
        title = driver.title.lower()
        
        # Check for timeout/connection error indicators
        timeout_indicators = [
            "this site can't be reached",
            "err_timed_out",
            "err_connection_timed_out",
            "took too long to respond",
            "connection timed out",
            "site can't be reached",
            "checking the connection",
            "checking the proxy"
        ]
        
        for indicator in timeout_indicators:
            if indicator in page_source or indicator in title:
                logger.warning(f"⏰ TIMEOUT/CONNECTION ERROR DETECTED!")
                logger.warning(f"   Indicator: '{indicator}'")
                logger.warning(f"   URL: {driver.current_url}")
                logger.warning(f"   Page title: {driver.title}")
                return True
                
        return False
        
    except Exception as e:
        logger.warning(f"⚠️ Error checking for timeout: {str(e)}")
        return False

def check_access_denied(driver):
    """
    More specific check for Access Denied pages (avoiding timeout false positives)
    """
    try:
        page_source = driver.page_source.lower()
        current_url = driver.current_url
        title = driver.title.lower()
        
        # First check if this is actually a timeout error
        if check_timeout_error(driver):
            return False, None  # Not access denied, just a timeout
        
        # More specific access denied indicators (avoiding timeout conflicts)
        access_denied_indicators = [
            "access denied",
            "you don't have permission to access",
            "reference #18.c",  # More specific reference pattern
            "forbidden",
            "error 403",
            "cloudflare ray id:",
            "why have i been blocked",
            "bot protection",
            "please complete the security check",
            "verify you are human",
            "security check",
            "anti-bot"
        ]
        
        # Check for multiple indicators to reduce false positives
        found_indicators = []
        for indicator in access_denied_indicators:
            if indicator in page_source:
                found_indicators.append(indicator)
        
        # Require more evidence for "blocked" detection
        if "blocked" in page_source:
            # Only consider it access denied if we also find other indicators
            blocking_context = [
                "you have been blocked",
                "your access has been blocked", 
                "this website is using a security service",
                "cloudflare",
                "reference #"
            ]
            if any(context in page_source for context in blocking_context):
                found_indicators.append("blocked (with context)")
        
        if found_indicators:
            # Try to extract reference number if present
            ref_number = "Unknown"
            if "reference #" in page_source:
                try:
                    ref_start = page_source.find("reference #") + len("reference #")
                    ref_end = page_source.find("<", ref_start)
                    if ref_end == -1:
                        ref_end = page_source.find(" ", ref_start)
                    if ref_end == -1:
                        ref_end = ref_start + 20
                    ref_number = page_source[ref_start:ref_end].strip()
                except:
                    pass
            
            logger.error(f"🚫 ACCESS DENIED DETECTED!")
            logger.error(f"   Indicators: {found_indicators}")
            logger.error(f"   URL: {current_url}")
            logger.error(f"   Reference: {ref_number}")
            logger.error(f"   Page title: {driver.title}")
            
            return True, ref_number
            
        return False, None
        
    except Exception as e:
        logger.warning(f"⚠️ Error checking for access denied: {str(e)}")
        return False, None

def has_contact_button(container):
    """
    Check if a container element has a contact button (indicating it's a real car listing)
    """
    contact_button_selectors = [
        'button[data-testid="listing-action-email"]',
    ]
    
    for selector in contact_button_selectors:
        try:
            button = container.find_element(By.CSS_SELECTOR, selector)
            if button and button.is_displayed():
                logger.debug(f"✅ Found contact button with selector: {selector}")
                return True
        except:
            continue
    
    return False

def logic_mobilede(PROXY: ProxyABC = EmptyProxy()):
    driver = None
    monitor = None
    start_time = datetime.now()
    validator = CarDataValidator()  # Initialize validator
    
    try:
        log_section("INITIALIZING PARSER")
        # Validate proxy
        if isinstance(PROXY, EmptyProxy):
            proxy = EmptyProxy()
            logger.info("🔌 No proxy provided, using direct connection")
        else:
            proxy = PROXY
            logger.info(f"🔌 Using proxy: {proxy.host}:{proxy.port}")

        # Create driver with validated proxy
        logger.info("🚗 Creating Selenium driver...")
        driver = BaseSeleniumDriver(
            executable_path=GLOBAL.PATH.CHROMEDRIVER_PATH,
            proxy=proxy,
            headless=False,
            window_size=(1200, 1000),
            logger=logger,
            user_agent=UserAgent().chrome
        )
        # _driver_instance = new_driver # REMOVED

        logger.info("⚙️ Initializing driver instance...")
        driver.create_instance()
        
        # Initialize and start background access denied monitor
        monitor = AccessDeniedMonitor(driver)
        monitor.start_monitoring()
        
        # Verify proxy is working
        log_section("VERIFYING PROXY CONNECTION")
        logger.info("🌐 Testing proxy connection...")
        driver.get("https://api.ipify.org")
        time.sleep(5)
        
        # Check for access denied on IP check page
        is_blocked, ref_number = check_access_denied(driver)
        if is_blocked:
            raise AccessDeniedError(f"Blocked during IP check with reference: {ref_number}")
        
        try:
            # Try to find the IP in a <pre> element first
            try:
                ip = driver.find_element(By.TAG_NAME, "pre").text.strip()
                logger.info(f"✅ Current IP address (from <pre>): {ip}")
            except Exception:
                # If <pre> element not found, try to get IP from page body
                try:
                    ip = driver.find_element(By.TAG_NAME, "body").text.strip()
                    # Clean up the IP - it should be just the IP address
                    import re
                    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                    ip_match = re.search(ip_pattern, ip)
                    if ip_match:
                        ip = ip_match.group()
                        logger.info(f"✅ Current IP address (from body): {ip}")
                    else:
                        raise Exception("No valid IP address found in page content")
                except Exception as body_error:
                    # If all else fails, check the page source for debugging
                    page_source = driver.page_source
                    logger.error(f"❌ Page content: {page_source[:500]}...")
                    raise Exception(f"Could not extract IP from page. Body error: {body_error}")
            
            if isinstance(proxy, Proxy):
                # For authenticated proxies, we can't easily predict the IP 
                # as it might be different from the proxy host IP
                if proxy.username and proxy.userpass:
                    logger.info(f"🔒 Authenticated proxy working - got IP: {ip}")
                else:
                    # For non-authenticated proxies, we can still check the IP
                    expected_ip = proxy.host
                    if ip != expected_ip:
                        logger.warning(f"⚠️ PROXY MISMATCH! Expected {expected_ip} but got {ip}")
                        logger.warning("Note: This might be normal for some proxy providers")
                    else:
                        logger.info(f"🔒 Proxy verified successfully ({ip} == {expected_ip})")
            else:
                logger.info("🔓 No proxy was provided, using direct connection")
                logger.debug(f"type(proxy): {type(proxy)}")
                logger.debug(f"Proxy: {Proxy}")
                logger.debug(f"proxy.__class__ == Proxy: {proxy.__class__ == Proxy}")
                logger.debug(f"isinstance(proxy, Proxy): {isinstance(proxy, Proxy)}")
                
        except Exception as e:
            logger.error(f"❌ Critical error checking IP: {str(e)}")
            raise

        log_section("STARTING PARSING")
        logger.info("🌐 Navigating to mobile.de...")
        driver.get("https://mobile.de/")
        print("Waiting for page to load...")
        try:
            # Wait for page to load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(10)
            
            # Check for access denied on main page
            is_blocked, ref_number = check_access_denied(driver)
            if is_blocked:
                raise AccessDeniedError(f"Blocked on main page with reference: {ref_number}")
            
            logger.info("✅ Page loaded successfully")
            
            # Get page source
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            
            # Find all car brand sections and filter for the one containing car brands
            logger.info("🔍 Searching for car brand sections...")
            car_brands_names_elements = driver.find_elements(By.CSS_SELECTOR, 'optgroup[label="Alle Marken"] > option')
            car_brands_names = [element.text for element in car_brands_names_elements]
            logger.info(f"✅ Found {len(car_brands_names)} car brands")
            logger.info(car_brands_names)
            
            car_brand_sections = soup.find_all('div', attrs={'data-testid': 'home-seo-links-items'})
            car_brand_section = None
            
            # Look for the section containing car brands by checking its content
            for section in car_brand_sections:
                links = section.find_all('a', attrs={'data-testid': 'home-seo-link'})
                if links and any('Gebrauchtwagen' in link.text for link in links):
                    car_brand_section = section
                    break
                    
            if not car_brand_section:
                raise Exception("❌ Could not find the car brands section")
                
            car_brand_sections = [car_brand_section]  # Replace the list with just the relevant section
            
            # Dictionary to store all car brands and their URLs
            car_brands = {}
            
            # Process each section
            for section in car_brand_sections:
                # Get all links in the section
                links = section.find_all('a', attrs={'data-testid': 'home-seo-link'})
                
                # Extract brand name and URL for each link
                for link in links:
                    brand_name = link.text.strip().replace(' Gebrauchtwagen', '')
                    brand_url = link.get('href')
                    car_brands[brand_name] = brand_url
            
            logger.info(f"✅ Found {len(car_brands)} car brands")
            for brand, url in car_brands.items():
                logger.info(f"{brand}: {url}")
            
            for brand in car_brands_names:
                # also add aditional brands that are not in the list
                if brand not in car_brands.keys():
                    #url example for 2 words brand https://suchen.mobile.de/auto/alfa-romeo.html
                    car_brands[brand] = f"https://suchen.mobile.de/auto/{brand.lower().replace(' ', '-')}.html"
                
            # Store the results in a more structured format if needed
            car_brands_data = {
                'total_brands': len(car_brands),
                'brands': car_brands
            }
            
            # Process each brand
            for brand, url in car_brands_data['brands'].items():
                
                # Check if background monitor detected access denied
                if monitor.is_access_denied():
                    detection_info = monitor.get_detection_info()
                    logger.error(f"🚨 Background monitor detected access denied!")
                    raise AccessDeniedError(f"Background monitor detection: {detection_info['ref_number']}")
                    
                log_section(f"PROCESSING BRAND: {brand}")
                logger.info(f"🌐 Navigating to {brand} at {url}")
                driver.get(url)
                
                # Wait for page load
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(10)  # Wait for page to fully load
                
                # Check for access denied immediately after navigation
                is_blocked, ref_number = check_access_denied(driver)
                if is_blocked:
                    logger.error(f"🚫 Access denied detected for brand {brand}")
                    time.sleep(10)
                    raise AccessDeniedError(f"Blocked on {brand} page with reference: {ref_number}")
                
                time.sleep(20)  # Additional wait time to ensure page loads completely
                
                # Check if we're on mobile version

                logger.info("✅ Detected desktop version of the site")
                # Get and parse page content
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, "html.parser")
                
                page_count = 0
                max_pages = 10  # Limit to 10 pages per brand to prevent infinite loops
                consecutive_empty_pages = 0
                max_consecutive_empty = 3  # Break if we hit 3 consecutive pages with no results
                previous_url = driver.current_url  # Track URL changes to detect successful pagination
                
                while page_count < max_pages and consecutive_empty_pages < max_consecutive_empty:
                    # Check if background monitor detected access denied
                    if monitor.is_access_denied():
                        detection_info = monitor.get_detection_info()
                        logger.error(f"🚨 Background monitor detected access denied while processing {brand}")
                        raise AccessDeniedError(f"Background monitor detection: {detection_info['ref_number']}")
                    
                    page_count += 1
                    logger.info(f"📄 Processing page {page_count} for {brand}")
                    
                    # Find all potential listing containers first
                    logger.info("🔍 Looking for all potential listing containers...")
                    potential_containers = []
                    
                    # Try different container selectors that might contain car listings
                    container_selectors = [
                        '[data-testid^="result-listing-"]',
                        'article[data-testid*="listing"]',
                        'div[data-testid*="listing"]',
                        'article[class*="listing"]',
                        'div[class*="listing"]',
                        'article[data-testid*="result"]',
                        'div[data-testid*="result"]'
                    ]
                    
                    for selector in container_selectors:
                        try:
                            containers = driver.find_elements(By.CSS_SELECTOR, selector)
                            potential_containers.extend(containers)
                        except:
                            continue
                    
                    logger.info(f"📦 Found {len(potential_containers)} potential containers")
                    
                    # Filter containers to only include those with contact buttons
                    search_results = []
                    for container in potential_containers:
                        if has_contact_button(container):
                            search_results.append(container)
                            logger.debug(f"✅ Container has contact button - added to search results")
                        else:
                            logger.debug(f"❌ No contact button found in container - skipping")
                            continue
                    
                    # Always check for access denied first, regardless of results
                    is_blocked, ref_number = check_access_denied(driver)
                    if is_blocked:
                        logger.error(f"🚫 Access denied detected on page {page_count} for {brand}")
                        time.sleep(10)
                        raise AccessDeniedError(f"Blocked on page {page_count} with reference: {ref_number}")
                    
                    if len(search_results) == 0:
                        consecutive_empty_pages += 1
                        logger.warning(f"⚠️ No car listings with contact buttons found for {brand} on page {page_count} (consecutive empty: {consecutive_empty_pages}/{max_consecutive_empty})")
                        
                        # If this is the first page and no results, the brand might not have listings
                        if page_count == 1:
                            logger.warning(f"⚠️ No listings found on first page for {brand} - skipping brand")
                            break
                        
                        # If we've hit too many consecutive empty pages, stop
                        if consecutive_empty_pages >= max_consecutive_empty:
                            logger.warning(f"⚠️ Hit {max_consecutive_empty} consecutive empty pages for {brand} - stopping search")
                            break
                        
                        # Try to find next page button before giving up on subsequent pages
                        try:
                            pagination_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Weiter') or @aria-label='Weiter']")
                            if pagination_button.is_displayed() and pagination_button.is_enabled():
                                logger.info("🔄 No results on this page but next page available - continuing...")
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pagination_button)
                                time.sleep(2)
                                driver.execute_script("arguments[0].click();", pagination_button)
                                time.sleep(10)
                                
                                # Check for access denied after empty page pagination
                                is_blocked, ref_number = check_access_denied(driver)
                                if is_blocked:
                                    logger.error(f"🚫 Access denied detected after empty page pagination")
                                    time.sleep(10)
                                    raise AccessDeniedError(f"Blocked after empty page pagination with reference: {ref_number}")
                                
                                continue
                            else:
                                logger.info("📄 No more pages available")
                                break
                        except:
                            logger.info("📄 No pagination button found - ending search for this brand")
                            break
                    else:
                        consecutive_empty_pages = 0  # Reset counter when we find results
                    logger.info(f"✅ Found {len(search_results)} actual car listings with contact buttons for {brand}")
                    
                    smart_parser_cooldown = 100
                    current_result_parsed = 0
                    
                    for idx, result in enumerate(search_results, 1):
                        # Check background monitor every few listings
                        if idx % 5 == 0:  # Check every 5 listings
                            if monitor.is_access_denied():
                                detection_info = monitor.get_detection_info()
                                logger.error(f"🚨 Background monitor detected access denied at listing {idx}")
                                raise AccessDeniedError(f"Background monitor detection: {detection_info['ref_number']}")
                        
                        # Reduced periodic explicit check (now background monitor handles most cases)
                        if idx % 50 == 0:  # Only check every 50 listings explicitly
                            is_blocked, ref_number = check_access_denied(driver)
                            if is_blocked:
                                logger.error(f"🚫 Access denied detected during explicit check at listing {idx}")
                                time.sleep(10)
                                raise AccessDeniedError(f"Blocked during explicit check with reference: {ref_number}")
                        
                        try:
                            logger.info(f"📄 Processing listing {idx}/{len(search_results)}")
                            # Scroll result into view
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", result)
                            time.sleep(1) # Short pause for scrolling to complete

                            # Attempt to click using JavaScript as a more robust method
                            logger.info("🖱️ Attempting JavaScript click on listing...")
                            driver.execute_script("arguments[0].click();", result)
                            time.sleep(2) # Pause after click
                            
                            # Store the main window handle
                            main_window = driver.current_window_handle
                            
                            # Switch to the new tab if one opened
                            if len(driver.window_handles) > 1:
                                new_window = [window for window in driver.window_handles if window != main_window][0]
                                driver.switch_to.window(new_window)
                                logger.info("🔄 Switched to new tab")
                            else:
                                logger.warning("⚠️ No new tab opened after click. Continuing on main window.")

                            # Wait for detail page to load with retry logic
                            max_retries = 3
                            retry_count = 0
                            page_loaded = False
                            
                            while retry_count < max_retries and not page_loaded:
                                try:
                                    # Wait for detail page to load (shorter timeout)
                                    WebDriverWait(driver, 15).until(
                                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                                    )
                                    time.sleep(3)
                                    
                                    # Check if it's a timeout error
                                    if check_timeout_error(driver):
                                        retry_count += 1
                                        if retry_count < max_retries:
                                            logger.warning(f"⏰ Timeout error detected. Retrying... ({retry_count}/{max_retries})")
                                            driver.refresh()
                                            time.sleep(5)
                                            continue
                                        else:
                                            logger.error(f"⏰ Failed to load page after {max_retries} retries - skipping listing")
                                            # Close current tab and switch back to main window
                                            if driver.current_window_handle != main_window:
                                                driver.close()
                                                driver.switch_to.window(main_window)
                                            continue  # Skip this listing
                                    
                                    # Check for access denied on detail page
                                    is_blocked, ref_number = check_access_denied(driver)
                                    if is_blocked:
                                        logger.error(f"🚫 Access denied detected on detail page for listing {idx}")
                                        # Close current tab and switch back to main window
                                        if driver.current_window_handle != main_window:
                                            driver.close()
                                            driver.switch_to.window(main_window)
                                        time.sleep(10)
                                        raise AccessDeniedError(f"Blocked on detail page with reference: {ref_number}")
                                    
                                    page_loaded = True
                                    
                                except Exception as e:
                                    retry_count += 1
                                    if retry_count < max_retries:
                                        logger.warning(f"⚠️ Error loading detail page. Retrying... ({retry_count}/{max_retries}): {str(e)}")
                                        time.sleep(5)
                                        continue
                                    else:
                                        logger.error(f"❌ Failed to load detail page after {max_retries} retries: {str(e)}")
                                        # Close current tab and switch back to main window
                                        if driver.current_window_handle != main_window:
                                            driver.close()
                                            driver.switch_to.window(main_window)
                                        continue  # Skip this listing
                            
                            if not page_loaded:
                                continue  # Skip to next listing
                            
                            # Get and parse detail page
                            detail_page = driver.page_source
                            detail_soup = BeautifulSoup(detail_page, "html.parser")
                            
                            # Final check to ensure we have proper content (not a timeout page)
                            if check_timeout_error(driver):
                                logger.warning(f"⏰ Still showing timeout error after retries - skipping listing {idx}")
                                # Close current tab and switch back to main window
                                if driver.current_window_handle != main_window:
                                    driver.close()
                                    driver.switch_to.window(main_window)
                                continue
                            
                            logger.info("✅ Successfully loaded detail page")
                            #===============================================
                            #=================KEY FEATURES==================
                            # Extract and store car details here
                            car_data = {
                                "basic_info": {},
                                "key_features": {}
                            }

                            # Extract basic info from main listing
                            try:
                                title = driver.find_element(By.XPATH, "//h2").text.strip()
                                title_brand = ""
                                title_model = ""
                                for brand in car_brands_names:
                                    if brand in title:
                                        title_brand = brand
                                        break
                                title_model = title.replace(title_brand, "").strip()
                                price = driver.find_element(By.XPATH, "//div[@data-testid='vip-price-label']").text.strip()
                                # extract mobile.de id from url and convert to int example: https://suchen.mobile.de/fahrzeuge/details.html?id=426053058&cn=DE&isSearchRequest=true&ms=1900%3B%3B%3B&od=up&pageNumber=2&ref=srp&refId=666a8756-1eae-924a-abc3-a76b00ec3f62&s=Car&sb=rel&searchId=666a8756-1eae-924a-abc3-a76b00ec3f62&vc=Car
                                mobile_de_id = int(driver.current_url.split("id=")[1].split("&")[0])
                                car_data["basic_info"] = {
                                    "brand": title_brand,
                                    "model": title_model,
                                    "title": title,
                                    "price": price,
                                    "url": driver.current_url,
                                    "mobile_de_id": mobile_de_id
                                }
                            except Exception as e:
                                logger.error(f"❌ Error extracting basic info: {str(e)}")

                            # Extract key features using data-testid attributes
                            car_data["key_features"] = {}
                            
                            # Find all key features using Selenium WebDriver
                            features = driver.find_element(By.CSS_SELECTOR, 'article[data-testid^="vip-key-features-box"]')
                            
                            # Try to get each feature individually
                            try:
                                mileage = features.find_element(By.CSS_SELECTOR, 'div[data-testid="vip-key-features-list-item-mileage"]').text.strip()
                                car_data["key_features"]["mileage"] = mileage
                            except:
                                car_data["key_features"]["mileage"] = "Not found"
                                
                            try:
                                power = features.find_element(By.CSS_SELECTOR, 'div[data-testid="vip-key-features-list-item-power"]').text.strip()
                                car_data["key_features"]["power"] = power
                            except:
                                car_data["key_features"]["power"] = "Not found"

                            try:
                                fuel_type = features.find_element(By.CSS_SELECTOR, 'div[data-testid="vip-key-features-list-item-fuel"]').text.strip()
                                car_data["key_features"]["fuel_type"] = fuel_type
                            except:
                                car_data["key_features"]["fuel_type"] = "Not found"
                                
                            try:
                                transmission = features.find_element(By.CSS_SELECTOR, 'div[data-testid="vip-key-features-list-item-transmission"]').text.strip()
                                car_data["key_features"]["transmission"] = transmission
                            except:
                                car_data["key_features"]["transmission"] = "Not found"
                                
                            try:
                                first_registration = features.find_element(By.CSS_SELECTOR, 'div[data-testid="vip-key-features-list-item-firstRegistration"]').text.strip()
                                car_data["key_features"]["first_registration"] = first_registration
                            except:
                                car_data["key_features"]["first_registration"] = "Not found"
                                
                            try:
                                number_of_previous_owners = features.find_element(By.CSS_SELECTOR, 'div[data-testid="vip-key-features-list-item-numberOfPreviousOwners"]').text.strip()
                                car_data["key_features"]["number_of_previous_owners"] = number_of_previous_owners
                            except:
                                car_data["key_features"]["number_of_previous_owners"] = "Not found"
                                
                            try:
                                battery_range = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="vip-key-features-list-item-batteryRange"]').text.strip()
                                car_data["key_features"]["battery_range"] = battery_range
                            except:
                                car_data["key_features"]["battery_range"] = "Not found"
                                
                            try:
                                warranty_registration = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="vip-key-features-list-item-warrantyRegistration"]').text.strip()
                                car_data["key_features"]["warranty_registration"] = warranty_registration
                            except:
                                car_data["key_features"]["warranty_registration"] = "Not found"

                            # Extract special "Technische Daten"
                            #===============TECHNICAL DATA==================
                            try:
                                # Find all dt elements with data-testid
                                dt_elements = driver.find_elements(By.CSS_SELECTOR, "dl dt[data-testid]")
                                # find expand button with better waiting and error handling
                                try:
                                    logger.info("🔍 Looking for expand buttons...")
                                    # Wait for buttons to be present and clickable
                                    expand_buttons = WebDriverWait(driver, 10).until(
                                        EC.presence_of_all_elements_located((By.XPATH, "//button[contains(text(), 'Mehr anzeigen')]"))
                                    )
                                    
                                    for expand_button in expand_buttons:
                                        try:
                                            # Scroll button into view
                                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", expand_button)
                                            time.sleep(1)
                                            
                                            # Wait for button to be clickable
                                            WebDriverWait(driver, 5).until(EC.element_to_be_clickable(expand_button))
                                            
                                            # Click using JavaScript to avoid interception issues
                                            driver.execute_script("arguments[0].click();", expand_button)
                                            logger.info("🔍 Successfully clicked expand button")
                                            time.sleep(2)  # Wait for content to expand
                                            
                                        except Exception as click_error:
                                            logger.warning(f"⚠️ Failed to click expand button: {str(click_error)}")
                                            continue
                                            
                                except Exception as find_error:
                                    logger.warning(f"⚠️ No expand buttons found or not clickable: {str(find_error)}")
                                    # Don't continue here, just proceed without expanding
                                
                                # Initialize technical data dictionary
                                car_data["technical_data"] = {}
                                
                                # Process each dt element
                                for dt in dt_elements:
                                    try:
                                        # Get the data-testid value
                                        data_testid = dt.get_attribute("data-testid")
                                        logger.info(f"🔍 Processing technical data field: {data_testid}")

                                        
                                        
                                        # Find the parent dl element
                                        dl = dt.find_element(By.XPATH, "./..")
                                        logger.debug(f"📑 Found parent dl element")
                                        
                                        # Find all dd elements within the same dl
                                        dd_elements = dl.find_elements(By.TAG_NAME, "dd")
                                        logger.debug(f"📑 Found {len(dd_elements)} dd elements")
                                        
                                        # Get the index of current dt element
                                        dt_index = dl.find_elements(By.TAG_NAME, "dt").index(dt)
                                        logger.debug(f"📑 Current dt index: {dt_index}")
                                        
                                        # Get corresponding dd element
                                        dd = dd_elements[dt_index]
                                        logger.debug(f"📑 Found corresponding dd element: {dd.text}")
                                        
                                        # Extract text values
                                        key = data_testid
                                        value = dd.text.strip()
                                        if value == "":
                                            value = dd.text
                                        logger.info(f"✅ Extracted {key}: {value}")
                                        
                                        # Store in technical_data dictionary
                                        car_data["technical_data"][key] = value
                                        logger.debug(f"💾 Stored {key} in technical_data dictionary")
                                        
                                    except Exception as e:
                                        logger.warning(f"Failed to extract technical data pair for {data_testid}: {str(e)}")
                                        continue
                                        
                            except Exception as e:
                                logger.error(f"Failed to extract technical data section: {str(e)}")
                                car_data["technical_data"] = {}
                            #============================================
                            #=================EQUIPMENT==================
                            try:
                                logger.info("🔍 Looking for equipment section...")
                                equipment_section = driver.find_element(By.CSS_SELECTOR, 'article[data-testid="vip-features-box"]')
                                
                                # Find the features list
                                features_list = equipment_section.find_element(By.CSS_SELECTOR, 'ul[data-testid="vip-features-list"]')
                                
                                # Get all list items
                                equipment_items = features_list.find_elements(By.CSS_SELECTOR, 'li')
                                
                                # Extract text from each item
                                equipment = [item.text.strip() for item in equipment_items if item.text.strip()]
                                
                                # Store in car_data as dictionary with True values
                                car_data["equipment"] = {item: True for item in equipment}
                                
                                if equipment:
                                    logger.info(f"✅ Extracted {len(equipment)} equipment items: {equipment}")
                                else:
                                    logger.warning("⚠️ Found equipment section but no items detected")
                                
                            except Exception as e:
                                logger.warning(f"⚠️ Failed to extract equipment: {str(e)}")
                                car_data["equipment"] = {}
                            #============================================
                            #=================LOCATION==================
                            try:
                                logger.info("🔍 Looking for location section...")
                                # Find the map info popup using static data-testid
                                location_popup = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="dealer-map-info-popup"]')
                                # Find address by position relative to known elements
                                address_span = location_popup.find_element(By.XPATH, './/span[preceding-sibling::b and following-sibling::a]')
                                car_data["basic_info"]["location"] = address_span.text.strip()
                                logger.info(f"✅ Extracted location: {car_data['basic_info']['location']}")
                            except Exception as e:
                                logger.warning(f"⚠️ Failed to extract location: {str(e)}")
                                car_data["basic_info"]["location"] = ""
                            #============================================
                            
                            # Store the data instead of printing
                            # TODO: Add your storage logic here (database, file, etc.)
                            logger.info("📦 Extracted car data:")
                            logger.info(car_data)
                            
                            # Check for duplicates before validation
                            is_duplicate = False
                            
                            # Check if car already exists in raw data by mobile_de_id
                            try:
                                with open("raw_cars_data.json", "r", encoding="utf-8") as f:
                                    raw_data = json.load(f)
                                    if car_data["basic_info"]["mobile_de_id"] in [item["basic_info"]["mobile_de_id"] for item in raw_data]:
                                        logger.info("🔍 Car already exists in raw_cars_data.json - skipping")
                                        is_duplicate = True
                            except (FileNotFoundError, json.JSONDecodeError):
                                raw_data = []
                            
                            # Skip this car if it's a duplicate
                            if not is_duplicate:
                                
                                # Validate the extracted data
                                try:
                                    logger.info("🔧 Validating extracted data...")
                                    validated_data = validator.validate(car_data)
                                    logger.info("📦 Validated car data:")
                                    logger.info(validated_data)

                                    # === RAW DATA ===
                                    raw_data.append(car_data)
                                    with open("raw_cars_data.json", "w", encoding="utf-8") as f:
                                        json.dump(raw_data, f, ensure_ascii=False, indent=2)

                                    # === VALIDATED DATA ===
                                    try:
                                        with open("validated_cars_data.json", "r", encoding="utf-8") as f:
                                            validated_list = json.load(f)
                                    except (FileNotFoundError, json.JSONDecodeError):
                                        validated_list = []

                                    validated_list.append(validated_data)
                                    with open("validated_cars_data.json", "w", encoding="utf-8") as f:
                                        json.dump(validated_list, f, ensure_ascii=False, indent=2)

                                except Exception as validation_error:
                                    logger.error(f"❌ Validation failed: {str(validation_error)}")

                                    # Save only to raw_cars_data.json even on validation failure
                                    raw_data.append(car_data)
                                    with open("raw_cars_data.json", "w", encoding="utf-8") as f:
                                        json.dump(raw_data, f, ensure_ascii=False, indent=2)

                            #============================================
                            
                            # Close current tab and switch back to main window (if a new tab was opened)
                            if driver.current_window_handle != main_window:
                                driver.close()
                                driver.switch_to.window(main_window)
                                logger.info("🚪 Closed tab and switched back to main window")
                            time.sleep(30) # Pause after switching back
                            
                            current_result_parsed += 1
                            if current_result_parsed >= smart_parser_cooldown:
                                logger.info("⏳ Cooldown period reached. Waiting 120 seconds...")
                                
                                # Check background monitor during cooldown (every 10 seconds)
                                for i in range(12):  # 12 * 10 = 120 seconds
                                    time.sleep(10)
                                    if monitor.is_access_denied():
                                        detection_info = monitor.get_detection_info()
                                        logger.error(f"🚨 Background monitor detected access denied during cooldown")
                                        raise AccessDeniedError(f"Background monitor detection during cooldown: {detection_info['ref_number']}")
                                
                                current_result_parsed = 0
                                
                        except Exception as e:
                            logger.error(f"❌ Error processing listing: {str(e)}")
                            # Make sure we're back on the main window if something goes wrong
                            try:
                                if len(driver.window_handles) > 1:
                                    driver.close()
                                driver.switch_to.window(main_window)
                            except:
                                pass
                            continue
                    # Try to find and click next page button
                    try:
                        pagination_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Weiter') or @aria-label='Weiter']")
                        # Check if pagination button is displayed and enabled
                        if pagination_button.is_displayed() and pagination_button.is_enabled():
                            # Scroll to pagination button
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pagination_button)
                            time.sleep(2)
                            # Click pagination button using javascript
                            driver.execute_script("arguments[0].click();", pagination_button)
                            logger.info(f"🔄 Clicked next page button, waiting for page {page_count + 1} to load...")
                            time.sleep(10)
                            
                            # Check for access denied after pagination
                            is_blocked, ref_number = check_access_denied(driver)
                            if is_blocked:
                                logger.error(f"🚫 Access denied detected after pagination click")
                                time.sleep(10)
                                raise AccessDeniedError(f"Blocked after pagination with reference: {ref_number}")
                            
                            # Verify page actually changed by checking URL
                            current_url = driver.current_url
                            if current_url == previous_url:
                                logger.warning("⚠️ URL didn't change after pagination click - may have reached the end")
                                break
                            previous_url = current_url
                            continue
                        else:
                            logger.info(f"📄 Next page button not available - reached end of results for {brand}")
                            break
                    except Exception as e:
                        logger.info(f"📄 No more pages available for {brand}: {str(e)}")
                        break
                
                logger.info(f"✅ Successfully processed {brand} ({page_count} pages)")
                    
        except Exception as e:
            logger.error(f"❌ Error waiting for page load: {str(e)}")
            raise

    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        raise
    finally:
        # Stop background monitor first
        if monitor:
            monitor.stop_monitoring()
            
        if driver:
            logger.info("🔄 Cleaning up driver...")
            try:
                driver.quit()
                logger.info("✅ Driver quit successfully")
            except Exception as e:
                logger.error(f"❌ Error while quitting driver: {str(e)}")
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"⏱️ Total execution time: {duration}")



