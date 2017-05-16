# -*- coding: utf-8 -*-
import logging
import os
from flask import Flask
import flask_restful
import constants
from robotwriter import controller

import requests
from requests.packages.urllib3.exceptions import (InsecureRequestWarning,
                                                  InsecurePlatformWarning)
# from datetime import timedelta
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
logging.getLogger('requests.packages.urllib3').setLevel(logging.WARN)


def get_config():
    """
        get config from envorinment variables -> dict
    """
    template_path = os.path.join(os.getcwd(), 'robotwriter/templates')
    ret = dict()
    ret = {
        constants.CFG_CONTENT_SERVER: os.environ.get(
            constants.ENV_CONTENT_SERVER,
            constants.CONTENT_SERVER_DEFAULT
        ),
        constants.CFG_CONTENT_KEY: os.environ.get(
            constants.ENV_CONTENT_KEY,
            constants.CONTENT_KEY_DEFAULT
        ),
        constants.CFG_WEATHER_TEMPLATE: os.path.join(template_path, 'weather'),
        constants.CFG_SOCCER_TEMPLATE: os.path.join(template_path, 'soccer'),
        constants.CFG_TIMEINFO_TEMPLATE: os.path.join(template_path, 'timeinfo'),
    }

    return ret

api = Flask(__name__)
restful_set = flask_restful.Api(api)

# get server config
config = get_config()

#setup api controller
controller.setup_route(config, restful_set)
