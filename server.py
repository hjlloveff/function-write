# -*- coding: utf-8 -*-
import os
from flask import Flask
import flask_restful
import constants
from robotwriter import controller


def get_config():
    """
        get config from envorinment variables -> dict
    """
    ret = dict()
    #ret = {
    #    constants.CFG_DB_SERVER: os.environ.get(
    #        constants.ENV_DB_SERVER,
    #        constants.DB_SERVER_DEFAULT
    #    ),
    #    constants.CFG_DB_USER: os.environ.get(
    #        constants.ENV_DB_USER,
    #        constants.DB_USER_DEFAULT
    #    ),
    #    constants.CFG_DB_PASSWORD: os.environ.get(
    #        constants.ENV_DB_PASSWORD,
    #        constants.DB_PASSWORD_DEFAULT
    #    ),
    #    constants.CFG_REDIS_SERVER: os.environ.get(
    #        constants.ENV_REDIS_SERVER,
    #        constants.REDIS_SERVER_DEFAULT
    #    ),
    #    constants.CFG_REDIS_DB: os.environ.get(
    #        constants.ENV_REDIS_DB,
    #        constants.REDIS_DB_DEFAULT
    #    ),
    #    constants.CFG_SYNONYM_PATH: constants.SYNONYM_PATH_DEFAULT,
    #    constants.CFG_TOPIC_PATH: constants.TOPIC_PATH_DEFAULT
    #}

    return ret

api = Flask(__name__)
restful_set = flask_restful.Api(api)

# get server config
config = get_config()

#setup api controller
controller.setup_route(config, restful_set)
