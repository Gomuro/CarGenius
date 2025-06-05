import os

import psutil
from PyQt6.QtWidgets import QMessageBox
from webdriver_manager.chrome import ChromeDriverManager

from src.GLOBAL import GLOBAL


class ChromeDriverDownloader:

    @classmethod
    def download(cls):
        try:
            for proc in psutil.process_iter():
                name = proc.name().lower()
                if "chrome" in name:
                    proc.terminate()

            if os.path.exists(GLOBAL.PATH.CHROMEDRIVER_PATH):
                os.remove(GLOBAL.PATH.CHROMEDRIVER_PATH)

            driver_path = ChromeDriverManager().install()
            os.rename(driver_path, GLOBAL.PATH.CHROMEDRIVER_PATH)
        except Exception as ex:
            QMessageBox.critical(None, "Error", str(ex))