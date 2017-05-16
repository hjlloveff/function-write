# -*- coding: utf-8 -*-
import logging

from .exception import ClientError
from .httpclient import do_get_request
from .common import time_calc_decorator


class SoccerService(object):
    def __init__(self, config):
        assert isinstance(config, dict), 'config %s is not dict' % config
        assert config.get('server_url')
        assert config.get('api_key')

        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    def server_url(self):
        return self.config['server_url']

    @property
    def api_key(self):
        return self.config['api_key']

    @time_calc_decorator
    def query(self, params):
        headers = {
            'Authorization': self.api_key
        }
        url = '%s/soccer' % self.server_url
        resp = do_get_request(url, headers=headers, params=params)
        self.logger.debug('resp: %s', resp)
        try:
            resp.raise_for_status()
        except Exception as exp:
            self.logger.exception('')
            raise ClientError(exp)
        return resp.content


# if __name__ == '__main__':
#     import logging.config
#     import os
#
#     import requests
#     from requests.packages.urllib3.exceptions import (InsecureRequestWarning,
#                                                       InsecurePlatformWarning)
#     # from datetime import timedelta
#     requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
#     requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
#     logging.getLogger('requests.packages.urllib3').setLevel(logging.WARN)
#
#     log_dict = {
#         'version': 1,
#         'disable_existing_loggers': False,
#         'root': {
#             'level': 'DEBUG',
#             'handlers': ['console']
#         },
#         'handlers': {
#             'console': {
#                 'class': 'logging.StreamHandler',
#                 'formatter': 'detail',
#                 'level': 'DEBUG'
#             },
#             'file': {
#                 'class': 'logging.handlers.RotatingFileHandler',
#                 'formatter': 'detail',
#                 'level': 'INFO',
#                 'filename': 'info.log',
#                 'maxBytes': 10 * 1024 * 1024,
#                 'backupCount': 10
#             }
#         },
#         'formatters': {
#             'detail': {
#                 'format': u'[%(asctime)s][%(threadName)10.10s]'
#                 '[%(levelname).1s][%(filename)s:%(funcName)s:%(lineno)s]:'
#                 ' %(message)s'
#             },
#             'simple': {
#                 'format': u'[%(asctime)s][%(threadName)10.10s]'
#                 '[%(levelname).1s][%(filename)s:%(lineno)s]: %(message)s'
#             }
#         }
#     }
#     logging.config.dictConfig(log_dict)
#
#     server_url = 'https://content-sh.emotibot.com'
#     api_key = u'2WDGS5SCH68RWDLC76BI9J6CZEKJM5QM'
#     update_interval = 60
#     config = {
#         'server_url': 'https://content-sh.emotibot.com',
#         'api_key': u'2WDGS5SCH68RWDLC76BI9J6CZEKJM5QM',
#     }
#
#     service = SoccerService(config)
#     params = {
#         u'team1': u'利物浦',
#         u'type': u'match'
#     }
#     import json
#     resp = service.query(team1=u'利物浦', type=u'match')
#     print dir(resp)
#     print '%s(%s): %s' % (resp, type(resp), json.dumps(json.loads(resp), ensure_ascii=False))
