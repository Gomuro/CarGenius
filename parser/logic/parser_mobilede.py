import json
import time
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

def logic_mobilede(PROXY: ProxyABC = EmptyProxy()):
    driver = None
    start_time = datetime.now()
    
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
        
        # Verify proxy is working
        log_section("VERIFYING PROXY CONNECTION")
        logger.info("🌐 Testing proxy connection...")
        driver.get("https://api.ipify.org")
        time.sleep(5)
        try:
            ip = driver.find_element(By.TAG_NAME, "pre").text
            logger.info(f"✅ Current IP address: {ip}")
            
            if isinstance(proxy, Proxy):
                expected_ip = proxy.host
                if ip != expected_ip:
                    logger.warning(f"⚠️ PROXY MISMATCH! Expected {expected_ip} but got {ip}")
                    logger.error("❌ Proxy verification failed - using direct connection")
                    # raise ValueError("Proxy IP mismatch detected")
                else:
                    logger.info(f"🔒 Proxy verified successfully ({ip} == {expected_ip})")
            else:
                logger.info("🔓 no proxy was provided skipping this proxy")
                print(f"type(proxy): {type(proxy)}")
                print(f"Proxy: {Proxy}")
                print(f"proxy.__class__ == Proxy: {proxy.__class__ == Proxy}")
                print(f"isinstance(proxy, Proxy): {isinstance(proxy, Proxy)}")
                # raise NoProxyProvidedError("No proxy provided - removing this proxy")
                
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
            logger.info("✅ Page loaded successfully")
            
            # Get page source
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            
            # Find all car brand sections and filter for the one containing car brands
            logger.info("🔍 Searching for car brand sections...")
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
                
            # Store the results in a more structured format if needed
            car_brands_data = {
                'total_brands': len(car_brands),
                'brands': car_brands
            }
            
            # Process each brand
            for brand, url in car_brands_data['brands'].items():
                log_section(f"PROCESSING BRAND: {brand}")
                # try:
                logger.info(f"🌐 Navigating to {brand} at {url}")
                driver.get(url)
                
                # Wait for page load
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                # Check for access denied page
                page_source = driver.page_source
                if "Access Denied" in page_source and "Reference #" in page_source:
                    ref_start = page_source.find("Reference #") + len("Reference #")
                    ref_end = page_source.find("<", ref_start)
                    ref_number = page_source[ref_start:ref_end].strip()
                    logger.error(f"🚫 Access denied detected (Ref: {ref_number})")
                    time.sleep(10)
                    raise AccessDeniedError(f"Blocked with reference: {ref_number}")
                time.sleep(30)  # Increased wait time to ensure page loads completely
                
                # Check if we're on mobile version
                if "m.mobile.de" in driver.current_url:
                    logger.warning("⚠️ Detected mobile version of the site")
                    logger.info("⏳ Waiting 10 minutes before trying next proxy...")
                    time.sleep(600)  # 10 minutes wait
                    raise Exception("Mobile version detected - switching proxy")
                
                # Get and parse page content
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, "html.parser")
                
                # Find all car listings using Selenium instead of BeautifulSoup
                search_results = WebDriverWait(driver, 30).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid^="result-listing-"]'))
                )
                
                logger.info(f"✅ Found {len(search_results)} listings for {brand}")
                
                smart_parser_cooldown = 10
                current_result_parsed = 0
                
                for idx, result in enumerate(search_results, 1):
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

                        # Wait for detail page to load
                        WebDriverWait(driver, 30).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        time.sleep(5)
                        
                        # Get and parse detail page
                        detail_page = driver.page_source
                        detail_soup = BeautifulSoup(detail_page, "html.parser")
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
                            price = driver.find_element(By.XPATH, "//div[@data-testid='vip-price-label']").text.strip()
                            car_data["basic_info"] = {
                                "title": title,
                                "price": price,
                                "url": driver.current_url
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
                            # find expand button
                            try:
                                expand_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Mehr anzeigen')]")
                                for expand_button in expand_buttons:
                                    expand_button.click()
                                    logger.info("🔍 Clicked expand button")
                                    time.sleep(1)
                            except:
                                logger.warning("⚠️ No expand button found")
                                continue
                            
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
                        #============================================
                        #==============JSON STORAGE==================
                        with open(f"car_data_{brand}_{idx}.json", "w") as f:
                            json.dump(car_data, f)
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
                            time.sleep(120)
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
                logger.info(f"✅ Successfully processed {brand}")
                    
                # except Exception as e:
                #     logger.error(f"❌ Error processing {brand}: {str(e)}")
                #     continue  # Continue with next brand even if one fails
            
        except Exception as e:
            logger.error(f"❌ Error waiting for page load: {str(e)}")
            raise

    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        raise
    finally:
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



