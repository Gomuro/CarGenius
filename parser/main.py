import sys
import os
import requests
from datetime import datetime
import logging
from logic.parser_mobilede import logic_mobilede
from proxy import Proxy, EmptyProxy
from parser.exceptions.driver import AccessDeniedError, NoProxyProvidedError  # Add at top

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def log_section(title):
    """Helper function to create section headers in logs"""
    logger.info(f"\n{'='*50}\n{title}\n{'='*50}")

if __name__ == "__main__":
    start_time = datetime.now()
    log_section("PROXY TESTING")
    
    # Read and filter valid proxies
    logger.info("📋 Reading proxy list...")
    with open("proxy.txt", "r") as file:
        proxy_list_str = [line.strip() for line in file.readlines() if line.strip() and ':' in line]
    
    if not proxy_list_str:
        logger.error("❌ No valid proxies found in proxy.txt")
        exit(1)
    
    logger.info(f"✅ Found {len(proxy_list_str)} valid proxies")
    
    # Check if proxy is working with error handling
    for idx, proxy_str in enumerate(proxy_list_str, 1):
        try:
            host, port_str = proxy_str.split(":")
            port = int(port_str)
            
            proxy_dict_for_requests = {
                'http': f'http://{host}:{port}',
                'https': f'http://{host}:{port}'
            }
            
            logger.info(f"🔍 Testing proxy {idx}/{len(proxy_list_str)}: {host}:{port}")
            response = requests.get("https://api.ipify.org", proxies=proxy_dict_for_requests, timeout=10)
            response.raise_for_status()
            logger.info(f"✅ Proxy check successful. IP: {response.text}")
            
            active_proxy = Proxy(host=host, port=port)
            log_section("STARTING PARSER")
            logic_mobilede(active_proxy)
            break
            
        except ValueError as e:
            logger.error(f"❌ Invalid proxy format: {proxy_str} - {str(e)}")
            continue
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Proxy {proxy_str} failed: {str(e)}")
            # Remove failed proxy from file
            try:
                with open("proxy.txt", "r") as file:
                    lines = file.readlines()
                with open("proxy.txt", "w") as file:
                    file.writelines([line for line in lines if line.strip() != proxy_str])
                logger.info(f"🗑️ Removed failed proxy {proxy_str} from proxy.txt")
            except Exception as e:
                logger.error(f"❌ Failed to remove proxy from file: {str(e)}")
            continue
        except AccessDeniedError as e:
            logger.error(f"❌ Access denied blocked detected: {str(e)}")
            # Remove failed proxy from file
            try:
                with open("proxy.txt", "r") as file:
                    lines = file.readlines()
                with open("proxy.txt", "w") as file:
                    file.writelines([line for line in lines if line.strip() != proxy_str])
                logger.info(f"🗑️ Removed blocked proxy {proxy_str} from proxy.txt")
            except Exception as file_error:
                logger.error(f"❌ Failed to remove proxy from file: {str(file_error)}")
            continue
        except NoProxyProvidedError as e:
            logger.info(f"🔓 No proxy provided - removing this proxy: {str(e)}")
            # Remove failed proxy from file
            try:
                with open("proxy.txt", "r") as file:
                    lines = file.readlines()
                with open("proxy.txt", "w") as file:
                    file.writelines([line for line in lines if line.strip() != proxy_str])
                logger.info(f"🗑️ Removed no proxy provided proxy {proxy_str} from proxy.txt")
            except Exception as file_error:
                logger.error(f"❌ Failed to remove proxy from file: {str(file_error)}")
            continue
        except Exception as e:
            logger.error(f"❌ Unexpected error with proxy {proxy_str}: {str(e)}")
            continue
    else:
        logger.warning("⚠️ All proxies failed. Running with direct connection.")
        log_section("STARTING PARSER (DIRECT CONNECTION)")
        logic_mobilede(EmptyProxy())
    
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"⏱️ Total execution time: {duration}")

