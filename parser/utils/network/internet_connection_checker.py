import time
from threading import Thread

import requests
from PyQt6.QtCore import QObject, pyqtSignal

from src.proxy import ProxyABC


class BackgroundInternetConnectionChecker(QObject, Thread):
    bad_internet_connection_signal = pyqtSignal()

    def __init__(self, proxy: ProxyABC, logger):
        super(BackgroundInternetConnectionChecker, self).__init__()
        self.proxy = proxy
        self.logger = logger
        self.running = False

    def run(self):
        self.running = True
        self.__mainloop()

    def stop(self) -> None:
        self.running = False

    def __mainloop(self):
        self.logger.debug(f'check internet connection thread started')

        while self.running:
            try:
                proxy = self.proxy.to_selenium_wire_options()['proxy']
                del proxy['no_proxy']
                start_time = time.time()

                self.logger.debug('Requesting to www.google.com..')

                response = requests.get('https://www.google.com', proxies=proxy, timeout=60, verify=False)

                self.logger.debug(f'Response: {response}')

                if response.status_code == 408:
                    raise Exception("Timeout, status_code: 408")

                self.logger.info(f'Good internet connection. response time: {time.time() - start_time}')

            except Exception as error:
                self.logger.warning(f'Detected bad internet connection. error: {error}')
                self.bad_internet_connection_signal.emit()

            time.sleep(180)
