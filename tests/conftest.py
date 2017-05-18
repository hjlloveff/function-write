import logging

root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)
logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s][%(threadName)10.10s][%(levelname).1s]'
                    '[%(name)s.%(funcName)s:%(lineno)s] : %(message)s')

import requests
from requests.packages.urllib3.exceptions import (InsecureRequestWarning,
                                                                                                    InsecurePlatformWarning)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
