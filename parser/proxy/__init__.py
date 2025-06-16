import logging
import re
import time
import traceback
from abc import ABC, abstractmethod
from typing import Literal, Union
import urllib.error
import urllib.request

import httpx
import ping3
import ssl
import certifi

cert = ssl.create_default_context(cafile=certifi.where())


class ProxyABC(ABC):
    @abstractmethod
    def get_protocol(self) -> str | None:
        """
        :return: protocol if proxy is working or None if not
        """
        pass

    def to_user_format_string(self) -> str:
        """
        Convert the proxy configuration to a string in the format "ip:port[:username:password]".

        Returns:
            str: A string representation of the proxy configuration.
        """
        pass

    def to_proxy_url_format(self) -> str:
        """
        Returns proxy in selenium_wire options
        """
        pass

    def change_ip(self) -> bool:
        """
        Attempt to change the proxy IP address.
        This method should be implemented by concrete proxy classes that support IP rotation.
        
        Returns:
            bool: True if IP was successfully changed, False otherwise
        """
        return False


class EmptyProxy(ProxyABC):
    """
    Represents an empty proxy configuration with no specific values set.
    """

    def __init__(self):
        self.host: str | None = None
        self.port: int | None = None
        self.username: str | None = None
        self.userpass: str | None = None
        self.protocol: Literal["HTTP", "HTTPS", "SOCKS5"] | None = None

    def get_protocol(self) -> str | None:
        return None

    def to_user_format_string(self) -> str:
        return ""

    def to_proxy_url_format(self) -> str:
        return ''


class Proxy(ProxyABC):
    """
    Represents a proxy configuration with IP, port, protocol, and optional username and password.
    """

    def __init__(self,
                 host: str,
                 port: int,
                 username: str | None = None,
                 userpass: str | None = None):

        self.host = host
        self.port = port
        self.username = username
        self.userpass = userpass
        self.protocol = None
        self.logger = logging.getLogger(__name__)

    def __eq__(self, other):
        if not isinstance(other, Proxy):
            return False

        return (self.host == other.host and self.port == other.port and self.username == other.username
                and self.userpass == other.userpass)

    @staticmethod
    def get_current_ip(proxy_str: str, logger: logging.Logger):
        GET_IP_URL = 'https://api.ipify.org'
        try:
            client = httpx.Client(follow_redirects=True, proxy=proxy_str)
            ip_response = client.get(GET_IP_URL)
            ip_response.raise_for_status()
            ip_address = ip_response.text.strip()
            logger.debug(f"Current IP address: {ip_address}")
        except Exception as ex:
            logger.error(f"Error getting IP address at {GET_IP_URL}: {ex}")
            ip_address = None
        return ip_address

    def get_protocol(self) -> None | str:

        # Ping IP-Address
        ping_time = ping3.ping(f"{self.host}")

        if not ping_time:
            print("Can't ping proxy host. Check your proxy is correct and http or https protocol. Probably "
                         "proxy is blocked by geo")
        else:
            print(f"Host proxy ping response is {str(ping_time)}")

        # Test proxy protocols (HTTP, HTTPS) to determine which one is valid
        proxies_str = f'{self.username}:{self.userpass}@{self.host}:{self.port}'
        print(f'checking proxy: {self.host, self.port}')

        for protocol in ('http', 'https'):
            print(f'checking proxy protocol')
            proxies = {
                "socks5": f"{protocol}://{proxies_str}",
                "socks5": f"{protocol}://{proxies_str}"
            }
            print("proxy protocol initialized")
            for _ in range(3):
                try:
                    print(f"Check proxy try - {_ + 1}; protocol - {protocol}")
                    https_handler = urllib.request.HTTPSHandler(context=cert)
                    opener = urllib.request.build_opener(urllib.request.ProxyHandler(proxies), https_handler)
                    f = opener.open(f"https://httpbin.org/ip")
                    f.read(1)
                    print(f'proxy {self.host}:{self.port} is working')
                    print(f'proxy protocol for {self.host}:{self.port} is: {protocol}')
                    return protocol
                except urllib.error.URLError as error:
                    print(f"No response: {str(error)}")
                    time.sleep(1)
                    continue
                except Exception as error:
                    print(f"Sudden error:\n{traceback.format_exc()}")
                    time.sleep(1)
                    continue

    @staticmethod
    def check_socks5_validation(proxy_url: str = None):
        if proxy_url and not Proxy._is_valid_proxy_url(proxy_url):
            raise ValueError("Invalid proxy URL format. Expected string: 'socks5://username:password@host:port'")

    @staticmethod
    def _is_valid_proxy_url(proxy_url: str) -> bool:
        pattern = re.compile(r"^socks5://[a-zA-Z0-9_]+:[a-zA-Z0-9_]+@[a-zA-Z0-9_.-]+:\d+$")
        return bool(pattern.match(proxy_url))

    @staticmethod
    def from_user_format_string(proxy_string: str) -> Union[EmptyProxy, 'Proxy']:
        split_proxy = proxy_string.split(':')

        try:
            # Handle format: username:password@host:port
            if '@' in proxy_string:
                # Split by @ to separate credentials from host:port
                credentials_part, host_port_part = proxy_string.rsplit('@', 1)
                
                # Parse credentials (username:password)
                if ':' in credentials_part:
                    username, password = credentials_part.split(':', 1)
                else:
                    return EmptyProxy()
                
                # Parse host:port
                if ':' in host_port_part:
                    host, port_str = host_port_part.split(':', 1)
                    port = int(port_str)
                else:
                    return EmptyProxy()
                
                return Proxy(host=host, port=port, username=username, userpass=password)
            
            # Handle existing format: host:port:username:password
            elif len(split_proxy) == 4:
                return Proxy(host=split_proxy[0],
                             port=int(split_proxy[1]),
                             username=split_proxy[2],
                             userpass=split_proxy[3])

            # Handle format: host:port (no authentication)
            elif len(split_proxy) == 2:
                return Proxy(host=split_proxy[0],
                             port=int(split_proxy[1]))

            else:
                return EmptyProxy()
        except ValueError:
            return EmptyProxy()

    def to_user_format_string(self) -> str:
        proxy_string = f'{self.host}:{self.port}'

        if (self.username is not None
                and self.userpass is not None):
            proxy_string += f':{self.username}:{self.userpass}'

        return proxy_string

    def to_proxy_url_format(self):
        return f"socks5://{self.username}:{self.userpass}@{self.host}:{self.port}"

    def __str__(self):
        return (f"Proxy(host={self.host}, port={self.port}, "
                f"username={self.username}, password={'*' * len(self.userpass) if self.userpass else None})")

    def change_ip(self) -> bool:
        """
        Attempt to change the proxy IP address.
        For standard proxies, this might involve reconnecting to a rotating proxy service.
        
        Returns:
            bool: True if IP was successfully changed, False otherwise
        """
        try:
            # Get the current IP for comparison
            proxy_str = self.to_proxy_url_format()
            current_ip = self.get_current_ip(proxy_str, self.logger)
            
            # Wait a short time to allow for IP rotation on the provider's side
            time.sleep(5)
            
            # Re-fetch the IP to check if it changed
            new_ip = self.get_current_ip(proxy_str, self.logger)
            
            if current_ip != new_ip and new_ip is not None:
                self.logger.info(f"IP changed successfully: {current_ip} -> {new_ip}")
                return True
            
            # If IP didn't change automatically, we can attempt to force a reconnection
            # This is provider-specific and would need to be implemented based on the proxy service being used
            self.logger.warning(f"IP did not change automatically. Manual reconnection may be required.")
            return False
            
        except Exception as e:
            self.logger.error(f"Error changing IP address: {e}")
            return False
