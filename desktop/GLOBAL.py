import os
import json
from pathlib import Path
import logging
from datetime import datetime

class GLOBAL:
    class PATH:
        APPLICATION_ROOT = os.path.join(os.path.expanduser('~'), 'CarGeniusData')
        ROOT = Path(APPLICATION_ROOT)
        LOGS = ROOT / "logs"
        SETTINGS = ROOT / "settings"
        LICENSE_FILE = SETTINGS / "license.key"

    class LICENSE:
        @staticmethod
        def save_license_key(key: str):
            GLOBAL.PATH.LICENSE_FILE.parent.mkdir(exist_ok=True, parents=True)
            with open(GLOBAL.PATH.LICENSE_FILE, 'w') as f:
                f.write(key)

        @staticmethod
        def get_license_key() -> str:
            try:
                with open(GLOBAL.PATH.LICENSE_FILE, 'r') as f:
                    return f.read()
            except FileNotFoundError:
                return ""

    # Add API configuration
    API_BASE_URL = "http://localhost:8000"  # This can be changed for production
    LICENSE_VALIDATE_ENDPOINT = "/license/validate"

    class LOG:
        _logger = None

        @staticmethod
        def _setup_logger():
            if GLOBAL.LOG._logger is None:
                GLOBAL.PATH.LOGS.mkdir(exist_ok=True, parents=True)
                logger = logging.getLogger(__name__)
                logger.setLevel(logging.INFO)
                formatter = logging.Formatter('%(asctime)s - %(message)s')
                filename = datetime.now().strftime("app_%Y-%m-%d_%H-%M-%S.log")
                file_handler = logging.FileHandler(GLOBAL.PATH.LOGS / filename)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                GLOBAL.LOG._logger = logger

        @staticmethod
        def write_log(message: str):
            GLOBAL.LOG._setup_logger()
            GLOBAL.LOG._logger.info(message)

    @staticmethod
    def get_settings() -> dict:
        settings_file = GLOBAL.PATH.SETTINGS / "settings.json"
        try:
            with open(settings_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"theme": "light", "language": "en"}

    @staticmethod
    def save_settings(settings: dict):
        GLOBAL.PATH.SETTINGS.mkdir(exist_ok=True, parents=True)
        settings_file = GLOBAL.PATH.SETTINGS / "settings.json"
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=4)

# Initialize directories and default settings on import
GLOBAL.PATH.LOGS.mkdir(exist_ok=True, parents=True)
GLOBAL.PATH.SETTINGS.mkdir(exist_ok=True, parents=True)
if not (GLOBAL.PATH.SETTINGS / "settings.json").exists():
    GLOBAL.save_settings({"theme": "light", "language": "en"})
