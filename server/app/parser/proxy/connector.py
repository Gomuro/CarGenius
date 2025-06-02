import os
import shutil
import string
import random

from server.app.GLOBAL import GLOBAL
from . import Proxy




class ProxyConnectorExtension:
    def __init__(self, proxy: Proxy):


        

        unique_id = ''.join(random.choices(string.ascii_letters + string.digits, k=6))

        extension_file_dir = os.path.abspath(
            os.path.join(GLOBAL.PATH.APPLICATION_ROOT, 'proxy_extensions')
        )

        self.__ext_dir = os.path.join(extension_file_dir, f'{unique_id}-proxy-connector')


        if not isinstance(proxy, Proxy):

            return

        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"76.0.0"
        }
        """


        background_js = f"""
        let config = {{
            mode: "fixed_servers",
            rules: {{
                singleProxy: {{
                    scheme: "http",
                    host: "{proxy.host}",
                    port: parseInt({proxy.port})
                }},
                bypassList: ["localhost"]
            }}
        }};
        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
        """

        # Add authentication only if both username and password are provided
        if proxy.username and proxy.userpass:
            background_js += f"""
        function callbackFn(details) {{
            return {{
                authCredentials: {{
                    username: "{proxy.username}",
                    password: "{proxy.userpass}"
                }}
            }};
        }}
        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {{urls: ["<all_urls>"]}},
            ['blocking']
        );"""
        elif proxy.username or proxy.userpass:
            print("Warning: Proxy has partial credentials - only username or password provided")


        """
        Check is everything correct with the self.__zip_path
        """
        os.makedirs(self.__ext_dir, exist_ok=True)


        with (open(os.path.join(self.__ext_dir, 'manifest.json'), 'w') as m_fs,
              open(os.path.join(self.__ext_dir, 'background.js'), 'w') as b_fs):

            m_fs.write(manifest_json)

            b_fs.write(background_js)


    def get_extension_dir(self):

        return self.__ext_dir

    def remove_extension_dir(self):

        try:
            shutil.rmtree(self.__ext_dir)
        except Exception as ex:
            print(ex)

    def __del__(self):
        """
        Remove the extension dir if instance was deleted
        """
        self.remove_extension_dir()
