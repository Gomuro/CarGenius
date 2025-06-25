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
        CHAT_HISTORY_FILE = SETTINGS / "chat_history.json"

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

    class CHAT_HISTORY:
        @staticmethod
        def save_chat_history(chat_history: list):
            """Save chat history to a local JSON file."""
            GLOBAL.PATH.CHAT_HISTORY_FILE.parent.mkdir(exist_ok=True, parents=True)
            try:
                with open(GLOBAL.PATH.CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump(chat_history, f, indent=4, ensure_ascii=False)
                print(f"Chat history saved to {GLOBAL.PATH.CHAT_HISTORY_FILE}")
            except Exception as e:
                print(f"Failed to save chat history: {e}")

        @staticmethod
        def load_chat_history() -> list:
            """Load chat history from the local JSON file."""
            try:
                with open(GLOBAL.PATH.CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    print(f"Chat history loaded from {GLOBAL.PATH.CHAT_HISTORY_FILE}")
                    return history
            except FileNotFoundError:
                print("No chat history file found, starting with empty history")
                return []
            except Exception as e:
                print(f"Failed to load chat history: {e}")
                return []

        @staticmethod
        def clear_chat_history():
            """Clear the saved chat history."""
            try:
                if GLOBAL.PATH.CHAT_HISTORY_FILE.exists():
                    GLOBAL.PATH.CHAT_HISTORY_FILE.unlink()
                    print("Chat history cleared")
            except Exception as e:
                print(f"Failed to clear chat history: {e}")

    # Add API configuration
    API_BASE_URL = "http://localhost:8000"  # This can be changed for production
    API_PREFIX = "/api/v1"
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
