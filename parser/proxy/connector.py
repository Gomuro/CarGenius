import os
import shutil
import string
import random

# Try to import GLOBAL from different locations
try:
    from server.app.GLOBAL import GLOBAL
except ImportError:
    try:
        from GLOBAL import GLOBAL
    except ImportError:
        # Fallback: create a minimal GLOBAL class
        class GLOBAL:
            class PATH:
                APPLICATION_ROOT = os.path.join(os.path.expanduser('~'), 'CarGeniusData')

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

        # Updated manifest for Manifest V3 compatibility but keeping V2 for broader support
        manifest_json = """{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy Auth",
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
        "scripts": ["background.js"],
        "persistent": true
    },
    "minimum_chrome_version": "76.0.0"
}"""

        # Improved background.js with better proxy configuration
        background_js = f"""
console.log('Proxy extension loaded');

// Configure proxy settings
var config = {{
    mode: "fixed_servers",
    rules: {{
        singleProxy: {{
            scheme: "http",
            host: "{proxy.host}",
            port: parseInt({proxy.port})
        }},
        bypassList: []
    }}
}};

// Set proxy configuration
chrome.proxy.settings.set({{
    value: config, 
    scope: "regular"
}}, function() {{
    console.log('Proxy configured: {proxy.host}:{proxy.port}');
}});

// Handle authentication for authenticated proxies
"""

        # Add authentication only if both username and password are provided
        if proxy.username and proxy.userpass:
            background_js += f"""
var pendingRequests = {{}};

// Handle proxy authentication
chrome.webRequest.onAuthRequired.addListener(
    function(details) {{
        console.log('Auth required for:', details.url);
        
        // Avoid infinite loops
        if (pendingRequests[details.requestId]) {{
            delete pendingRequests[details.requestId];
            return {{}};
        }}
        
        pendingRequests[details.requestId] = true;
        
        return {{
            authCredentials: {{
                username: "{proxy.username}",
                password: "{proxy.userpass}"
            }}
        }};
    }},
    {{urls: ["<all_urls>"]}},
    ['blocking']
);

// Clean up completed requests
chrome.webRequest.onCompleted.addListener(
    function(details) {{
        delete pendingRequests[details.requestId];
    }},
    {{urls: ["<all_urls>"]}}
);

chrome.webRequest.onErrorOccurred.addListener(
    function(details) {{
        delete pendingRequests[details.requestId];
    }},
    {{urls: ["<all_urls>"]}}
);

console.log('Proxy authentication configured for user: {proxy.username}');
"""
        else:
            background_js += """
console.log('No authentication configured - using proxy without auth');
"""

        background_js += """
// Log proxy status
chrome.proxy.settings.get({}, function(config) {
    console.log('Current proxy settings:', config);
});
"""

        """
        Check is everything correct with the self.__zip_path
        """
        os.makedirs(self.__ext_dir, exist_ok=True)


        with (open(os.path.join(self.__ext_dir, 'manifest.json'), 'w') as m_fs,
              open(os.path.join(self.__ext_dir, 'background.js'), 'w') as b_fs):

            m_fs.write(manifest_json)

            b_fs.write(background_js)

        print(f"Proxy extension created at: {self.__ext_dir}")


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
