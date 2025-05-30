import requests
from server.app.parser.logic.parser_mobilede import logic_mobilede
from server.app.parser.proxy import Proxy

if __name__ == "__main__":
    # Read and filter valid proxies
    with open("proxy.txt", "r") as file:
        proxy_list_str = [line.strip() for line in file.readlines() if line.strip() and ':' in line]
    
    if not proxy_list_str:
        print("No valid proxies found in proxy.txt")
        exit(1)
    
    # Check if proxy is working with error handling
    for proxy_str in proxy_list_str:
        try:
            host, port_str = proxy_str.split(":")
            port = int(port_str)
            
            # Create a dictionary for requests library
            proxy_dict_for_requests = {
                'http': f'http://{host}:{port}',
                'https': f'http://{host}:{port}'
            }
            
            print(f"Checking proxy: {host}:{port}")
            response = requests.get("https://api.ipify.org", proxies=proxy_dict_for_requests, timeout=10)
            response.raise_for_status()
            print(f"Proxy check successful. IP: {response.text}. Using this proxy for the driver.")
            
            # Create Proxy object for logic_mobilede
            active_proxy = Proxy(host=host, port=port)
            logic_mobilede(active_proxy)
            break
            
        except ValueError as e:
            print(f"Invalid proxy format: {proxy_str} - {str(e)}")
            continue
        except requests.exceptions.RequestException as e:
            print(f"Proxy {proxy_str} failed: {str(e)}")
            continue
        except Exception as e:
            print(f"Unexpected error with proxy {proxy_str}: {str(e)}")
            continue
    else:
        print("All proxies failed. Running with direct connection.")
        from server.app.parser.proxy import EmptyProxy
        logic_mobilede(EmptyProxy())

