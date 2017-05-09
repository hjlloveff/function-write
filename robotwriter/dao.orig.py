# -*- coding: utf-8 -*-
'''Data access object
'''
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from threading import Thread, Event

from .httpclient import do_get_request


class CityNode(object):
    def __init__(self, mapping):
        super(CityNode, self).__init__()
        self.city_id = mapping['city_id']
        self.city_name = mapping['city_name']
        self.province = mapping['province']

    def __str__(self):
        return 'CityNode(city_id: %s, city_name: %s)' % (self.city_id,
                                                         self.city_name)


class WeatherDao(Thread):
    '''Connect to content server in time_interval to retrieve last weather data

    '''
    def __init__(self, config):
        super(WeatherDao, self).__init__()

        self.config = {
            'content_url': '',
            'content_api_key': '',
            'time_interval': 60 * 60,   # 1 hour
            'city_list_expire_interval': 60 * 60 * 24  # 1 day
        }
        self._init = False
        self._city_list = defaultdict(dict)
        self.city_weather = defaultdict(dict)
        self.config.update(config)
        self.event = Event()
        self.report = None
        self.daemon = True
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    def content_api_key(self):
        return self.config['content_api_key']

    @property
    def content_url(self):
        return self.config['content_url']

    @property
    def city_list(self):
        '''Return list of CityNode type list

        :example:
            >>>
            [
                CityNode(city_id: u'CN101010100', city_name: u'北京', province: u'北京')
            ]
        '''
        self._reload_city()
        return self._city_list['data']

    @property
    def time_interval(self):
        return self.config['time_interval']

    @property
    def city_expire_interval(self):
        return self.config['city_list_expire_interval']

    def _reload_city(self):

        def expire(dt_today, exp_time):
            return True if dt_today > exp_time else False

        def json_obj_hook(mapping):
            if 'city_id' in mapping:
                return CityNode(mapping)
            return mapping

        dt_today = datetime.today()
        if self._city_list and \
                not expire(dt_today, self._city_list['expire_time']):
            return

        url = '%s/weather/cities' % self.content_url
        headers = {
            'Authorization': '%s' % self.content_api_key
        }
        city_list = self._city_list
        try:
            resp = do_get_request(url, headers=headers)
            resp_json = resp.json(object_hook=json_obj_hook)
            city_list['update_time'] = dt_today
            city_list['expire_time'] = dt_today + \
                timedelta(seconds=self.city_expire_interval)
            city_list['data'] = resp_json
            city_list['name_id_mapping'] = defaultdict(list)
            for city in city_list['data']:
                city_list['name_id_mapping'][city.city_name].append(
                    {'city_id': city.city_id, 'province': city.province})
        except Exception:
            raise

    def _get_city_weather(self, city_id):
        '''get weather by city_id
        '''

        def json_obj_hook(mapping):
            # TODO(mike): unfinished.
            return mapping

        assert city_id and isinstance(city_id, unicode)

        url = '%s/weather/%s' % (self.content_url, city_id)
        headers = {
            'Authorization': '%s' % self.content_api_key
        }
        resp = do_get_request(url, headers=headers)
        resp.raise_for_status()
        return resp.json(object_hook=json_obj_hook)

    def _update_city_weather(self):
        report = dict()
        for city in self.city_list:
            city_id = city.city_id
            try:
                self.city_weather[city_id] = self._get_city_weather(city_id)
                report[city_id] = None
            except Exception as exp:
                self.logger.info('get %s failed. %s', city, exp)
                report[city_id] = exp
                continue
        return report

    def _get_city_id(self, city_name, province=None):
        name_id_mapping = self._city_list['name_id_mapping']

        l = name_id_mapping.get(city_name, list())
        if province:
            for city in l:
                if province == city['province']:
                    return [city['city_id']]
            return list()
        return [city['city_id'] for city in l]

    def run(self):
        while self._init is False or self.event.wait(self.time_interval):
            self._init = True
            self.logger.info('start to update city weather')
            try:
                self.report = self._update_city_weather()
            except Exception as exp:
                self.logger.info('end update city weather, failed: %s', exp)
                continue

            self.logger.info('end update city weather, %s', self.report)

    def get_weather(self, city_name, province=None):
        '''Return all weather of the city

        :city_name: unicode, target city name
        :type: unicode
        :province: the province target city belong to
        :type: unicode

        :return: the target city weather in a list
        :rtype: list of list

        :example:
            >>> get_weather(u'朝阳')
            [
                [
                    {'city_id': 'CN101010300', 'city_name': '朝阳', 'date': '2017-04-18', 'day_air_level': None, ...}, {'city_id': 'CN101...l': None, ...}
                    {'city_id': 'CN101...l': None, ...},
                    ...
                ],
                [
                    {'city_id': 'CN101071201', 'city_name': '朝阳', 'date': '2017-04-18', 'day_air_level': None, ...}, {'city_id': 'CN101...l': None, ...}
                    {'city_id': 'CN101...l': None, ...},
                    ...
                ],
                [
                    {'city_id': 'CN101060110', 'city_name': '朝阳', 'date': '2017-04-18', 'day_air_level': None, ...}, {'city_id': 'CN101...l': None, ...}
                    {'city_id': 'CN101...l': None, ...},
                ]
            ]

            >>> get_city_data(u'朝阳', province='辽宁')
            [
                [
                    {'city_id': 'CN101071201', 'city_name': '朝阳', 'date': '2017-04-18', 'day_air_level': None, ...}, {'city_id': 'CN101...l': None, ...}
                    {'city_id': 'CN101...l': None, ...},
                    ...
                ],
            ]
        '''
        assert isinstance(city_name, unicode)
        assert province is None or isinstance(province, unicode)

        city_ids = self._get_city_id(city_name, province)
        self.logger.debug('city_name: %s, city_id: %s', city_name, city_ids)

        ret = list()
        self.logger.debug('city_ids: %s', city_ids)
        for city_id in city_ids:
            r = self.city_weather.get(city_id)
            if r is None:
                r = self._get_city_weather(city_id)
            if r:
                self.city_weather[city_id] = r
                ret.append(r)
        return ret
