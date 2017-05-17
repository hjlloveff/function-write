# -*- coding: utf-8 -*-
import logging
from threading import Thread, Event

from .exception import ServiceError, NotFoundError
from .httpclient import do_get_request
from .common import time_calc_decorator


class WeatherDao(Thread):
    '''Do 2 things
    1) update weather from content.emotibot.com every {update_interval}
    2) cached weather data from content.emotibot.com and api for get data.
    '''
    def __init__(self, config, city_list=None):
        # city_list only for unit-test to passed.
        super(WeatherDao, self).__init__()
        # default options
        self.options = {
            'server_url': '',
            'api_key': '',
            'update_interval': 60 * 60,
            'start_immediately': True,
            'city_list_expire_interval': 60 * 60 * 24  # 1 day
        }

        self.options.update(config)

        assert self.options['server_url'], 'server_url is empty!'
        assert self.options['api_key'], 'api_key is empty!'
        assert isinstance(self.options['update_interval'], int), \
            'update_interval is not integer!'

        # at least 1hour
        if self.options['update_interval'] < 3600:
            self.options['update_interval'] = 3600

        self.daemon = True
        self.weather_cache = dict()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._event = Event()
        self._city_list = city_list if city_list else list()
        if self.start_immediately:
            self.start()

    @property
    def start_immediately(self):
        return self.options['start_immediately']

    @property
    def server_url(self):
        return self.options['server_url']

    @property
    def api_key(self):
        return self.options['api_key']

    @property
    def update_interval(self):
        return self.options['update_interval']

    @property
    def city_list(self):
        if not self._city_list:
            self._update_city_list()
        return self._city_list

    @time_calc_decorator()
    def _update_city_list(self):
        '''If error occurred while update_city_list, should raise error
        '''
        url = '%s/weather/cities' % self.server_url
        headers = {
            'Authorization': self.api_key
        }
        try:
            resp = do_get_request(url, headers=headers)
            resp.raise_for_status()
            self._city_list = resp.json()
        except Exception:
            self.logger.exception('')
            raise

    # @time_calc_decorator
    def _get_city_weather(self, city_id):
        headers = {
            'Authorization': self.api_key
        }
        url = '%s/weather/%s' % (self.server_url, city_id)
        resp = do_get_request(url, headers=headers)
        if resp.status_code == 404:
            raise NotFoundError(resp)
        resp.raise_for_status()
        return resp.json()

    @time_calc_decorator()
    def _get_all_city_weather(self):
        d = dict()
        len_city_list = len(self.city_list)
        for city in self.city_list:
            city_id = city['city_id']
            try:
                resp = self._get_city_weather(city_id)
            except NotFoundError:
                self.logger.info('city %s(%s) notfound on server',
                                 city_id, city.city_name)
                d[city_id] = []  # avoid get miss and call server again
                continue
            except Exception as exp:
                self.logger.error('get city(%s) failed.(%s)', city_id, exp)
                continue
            d[city_id] = resp
            self.logger.debug("%s/%s", len(d), len_city_list)
        return d

    def upsert_city_weather(self, city_id):
        try:
            resp = self._get_city_weather(city_id)
            self.logger.info('upsert weather_cache(%s) with %s records',
                             city_id, len(resp))
            self.weather_cache[city_id] = resp
            return resp
        except Exception:
            return []

    def run(self):
        '''Get city data from content server
        if city_id list is empty:
            get city_id list from content-server

        for all city_id:
            get weather from content-server
            update city_weather_data

        wait for next hour or 5mins if there city update failed.
        '''
        update_interval = self.update_interval
        self._event.set()
        while self._event.is_set() or self._event.wait(update_interval) is False:
            self._event.clear()
            update_interval = self.update_interval

            # if len(self._city_list) == 0:
            #    self._update_city_list()

            weather_cache_dict = self._get_all_city_weather()

            # check return data_cache
            wc = weather_cache_dict.get(u'CN101010100')
            if not weather_cache_dict or not wc or len(wc) < 14:
                self.logger.info('get CN101010100, records(%s) < 14', len(wc))

            # update weather data
            if weather_cache_dict:
                self.weather_cache = weather_cache_dict

    @time_calc_decorator()
    def get_records(self, city_id, min_date=None, max_date=None):
        '''Get data from cache, if miss, get from content_server

        return empty list means not found / server return empty
        '''
        self.logger.info('city_id: %s', city_id)
        res = self.weather_cache.get(city_id)
        if res:
            self.logger.info('[Use cache]: %s', len(res))
        else:
            res = self.upsert_city_weather(city_id)
            self.logger.info('get %s: %s', city_id,
                             None if res is None else len(res))

        d = dict()
        for wn in res:
            d[unicode(wn['date'])] = wn

        return d


# if __name__ == '__main__':
#     import logging.config
#     import requests
#     from requests.packages.urllib3.exceptions import (InsecureRequestWarning,
#                                                       InsecurePlatformWarning)
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
#         'api_key': u'2WDGS5SCH68RWDLC76BI9J6CZEKJM5QM'
#     }
#     dao = WeatherDao(config)
#     evt = Event()
#
#     print 'city list: %s' % len(dao.city_list)
#     res = dao.get_records(u'CN101010100', None, None)
#     for n in res:
#         print '%s' % (n)
#     assert len(res) >= 14
#
#     res = dao.get_records(u'CN101010999', None, None)
#     assert isinstance(res, dict) and len(res.keys()) == 0
#
#     while evt.wait(1.0) is False:  # timeout will return false
#         print '>> %s: %s' % (len(dao.weather_cache), dao.is_alive())
#     # dao.get_nodes("CN1010100")
