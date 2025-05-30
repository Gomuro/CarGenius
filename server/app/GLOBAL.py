import json
import os
import sys
from enum import Enum
from datetime import datetime


class GLOBAL:
    class PATH:
        APPLICATION_ROOT = os.path.join(os.path.expanduser('~'), 'CarGeniusData')
        CHROMEDRIVER_PATH = os.path.join(APPLICATION_ROOT, 'chromedriver.exe')
