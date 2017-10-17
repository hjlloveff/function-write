# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta

import jinja2

from .common import time_calc_decorator


class TimeInfoOutput(dict):
    def __init__(self, date, type_, time_name, lunar_date, festival,
                 lunar_str):
        self.date = date
        self.type_ = type_
        self.time_name = time_name
        self.lunar_date = lunar_date
        self.lunar_str = lunar_str
        self.festival = festival

        self['general'] = self._generate_general()
        self['user'] = self._generate_user()

    def _generate_general(self):
        today = datetime.today()
        date_datetime = datetime.strptime(self.date, '%Y%m%d').date()
        if self.lunar_date:
            lunar_datetime = datetime.strptime(self.lunar_date, '%Y%m%d').date()
        else:
            lunar_datetime = None

        output = {
            "time_name": self.time_name,
            "now": {
                "date": today.strftime("%Y-%m-%d"),
                "weekday": today.weekday() + 1,
                "hour": today.hour,
                "minute": today.minute,
            },
            "target_date": {
                "date": date_datetime.strftime('%Y-%m-%d'),
                "year": date_datetime.year,
                "month": date_datetime.month,
                "day": date_datetime.day,
                "weekday": date_datetime.weekday() + 1,
            },
            "query_type": self.type_,
            "lunar": {
                "str": self.lunar_str if self.lunar_str else None,
                "month": lunar_datetime.month if lunar_datetime else None,
                "day": lunar_datetime.day if lunar_datetime else None
            },
            "festival": self.festival
        }
        return output

    def _generate_user(self):
        return {
            "name": None,
            "language": None,
            "gender": None,
            "age": None,
            "has": {
                "car": None,
            },
            "preference": {
                "suggest_outdoor": None,
                "suggest_cloth": None,
                "suggest_car": None,
                "suggest_uv": None,
            },
            "usage_history": {
                "last_uv_suggestion": None,
            },
        }


class TimeInfoService(object):
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        template_path = config.get('timeinfo_template')
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_path),
            trim_blocks=True,
            lstrip_blocks=True,
            extensions=['jinja2.ext.do', ]
        )
        self.jinja_template = env.get_template('main.html')

        self.logger.info('config: %s', config)

    @time_calc_decorator()
    def query(self, date, type_, time_name=None, templating=True,
              lunar_date=None, festival=None, lunar_str=None):
        assert date and type_

        @time_calc_decorator()
        def apply_template(obj_template, output):
            return obj_template.render(output)

        self.logger.info('date: %s, type_: %s, time_name: %s, templating: %s'
                         ', lunar_date: %s, festival: %s',
                         date, type_, time_name, templating, lunar_date, festival)
        output = TimeInfoOutput(date, type_, time_name, lunar_date, festival,
                                lunar_str)
        if templating:
            return apply_template(self.jinja_template, output)
        return output


#if __name__ == '__main__':
#    import os
#
#    import logging.config
#    import requests
#    from requests.packages.urllib3.exceptions import (InsecureRequestWarning,
#                                                      InsecurePlatformWarning)
#    # from datetime import timedelta
#    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
#    requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
#    logging.getLogger('requests.packages.urllib3').setLevel(logging.WARN)
#
#    log_dict = {
#        'version': 1,
#        'disable_existing_loggers': False,
#        'root': {
#            'level': 'DEBUG',
#            'handlers': ['console']
#        },
#        'handlers': {
#            'console': {
#                'class': 'logging.StreamHandler',
#                'formatter': 'detail',
#                'level': 'DEBUG'
#            },
#            'file': {
#                'class': 'logging.handlers.RotatingFileHandler',
#                'formatter': 'detail',
#                'level': 'INFO',
#                'filename': 'info.log',
#                'maxBytes': 10 * 1024 * 1024,
#                'backupCount': 10
#            }
#        },
#        'formatters': {
#            'detail': {
#                'format': u'[%(asctime)s][%(threadName)10.10s]'
#                '[%(levelname).1s][%(filename)s:%(funcName)s:%(lineno)s]:'
#                ' %(message)s'
#            },
#            'simple': {
#                'format': u'[%(asctime)s][%(threadName)10.10s]'
#                '[%(levelname).1s][%(filename)s:%(lineno)s]: %(message)s'
#            }
#        }
#    }
#    logging.config.dictConfig(log_dict)
#    config = {
#        'timeinfo_template': os.path.join(os.path.dirname(__file__),
#                                          'templates/timeinfo')
#    }
#    service = TimeInfoService(config)
#
#    def basic_test(date, type_, time_name=None, lunar=None, festival=None):
#        print service.query(date, type_, time_name=time_name, lunar_date=lunar,
#                            festival=festival)
#
#    today = datetime.today()
#    today_str = today.strftime('%Y%m%d')
#    basic_test(today_str, 'md')
#    basic_test(today_str, 'mdw')
#    basic_test(today_str, 'HM')
#
#    tomorrow = today + timedelta(days=1)
#    tomorrow_str = tomorrow.strftime('%Y%m%d')
#
#    basic_test(tomorrow_str, 'w', time_name=u'明天')
