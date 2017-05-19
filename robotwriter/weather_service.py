# -*- coding: utf-8 -*-
import os
import re
import logging
from datetime import datetime, timedelta
from collections import defaultdict

import jinja2

from .dao import WeatherDao
from .common import time_calc_decorator


class CityQuery(object):
    def __init__(self, city_id, city_name, date, time_name, keywords, gender,
                 duration):
        self.city_id = city_id
        self.city_name = city_name
        self.date = date
        self.date_in_datetime = datetime.strptime(self.date, '%Y%m%d')
        self.time_name = time_name
        self.keywords = keywords if keywords else []
        self.gender = gender
        self.duration = duration if duration is not None else 1


class WeatherNodeDays(dict):
    def __init__(self):
        self['date'] = []
        self['day_sky'] = []
        self['day_wind_direction'] = []
        self['day_wind_level'] = []
        self['day_temperature'] = []
        self['night_sky'] = []
        self['night_wind_direction'] = []
        self['night_wind_level'] = []
        self['night_temperature'] = []
        self['aqi_level'] = []
        self['max_temperature'] = []
        self['min_temperature'] = []
        # super(WeatherNodeDays, self).__init__()

    def __setitem__(self, key, value):
        if key not in self.keys():
            super(WeatherNodeDays, self).__setitem__(key, [])  # default list
        l = self[key]
        l.append(value)
        super(WeatherNodeDays, self).__setitem__(key, l)

    def add(self, oneday_record):
        if not oneday_record:
            return
        for key in oneday_record.keys():
            if key not in ['date',
                           'day_sky', 'day_temperature',
                           'day_wind_direction', 'day_wind_level',
                           'night_sky', 'night_temperature',
                           'night_wind_direction', 'night_wind_level',
                           'aqi_level', 'max_temperature',
                           'min_temperature']:
                continue
            self[key] = oneday_record[key]


class WeatherNode(dict):
    def __init__(self):
        self['sky'] = None
        self['temperature'] = None
        self['min_temperature'] = None
        self['max_temperature'] = None
        self['wind_direction'] = None
        self['wind_level'] = None
        self['aqi'] = None
        self['aqi_text'] = None
        self['aqi_level'] = None
        self['uv'] = None
        self['rain_probability'] = None
        self['sun'] = {
            u'type': None,
            u'hour': None,
            u'minute': None
        }


class WeatherNodeNow(WeatherNode):
    def __init__(self, mapping=None):
        super(WeatherNodeNow, self).__init__()
        if mapping:
            self.update(mapping)
            self['aqi'] = mapping.get('now_aqi')
            self['temperature'] = mapping.get('now_temperature')
            self['wind_direction'] = mapping.get('now_wind_direction')


class WeatherNodeOneDay(WeatherNode):
    def __init__(self, mapping=None):
        super(WeatherNodeOneDay, self).__init__()
        if mapping:
            self.update(mapping)


class WeatherNodeFutureDays(WeatherNodeDays):
    def __init__(self, **kwargs):
        super(WeatherNodeFutureDays, self).__init__()
        if kwargs:
            for key in self.keys():
                self[key].append(kwargs.get(key))


class WeatherNodeDay(WeatherNode):
    def __init__(self, mapping=None):
        super(WeatherNodeDay, self).__init__()
        if mapping:
            self['sky'] = mapping.get('day_sky')
            self['temperature'] = mapping.get('day_temperature')
            self['wind_direction'] = mapping.get('day_wind_direction')
            self['wind_level'] = mapping.get('day_wind_level')
            self['aqi_text'] = mapping.get('day_air_level_cn')
            self['aqi_level'] = mapping.get('day_air_level')
            self['sun'].update({
                u'type': mapping.get('day_sun_type'),
                u'hour': mapping.get('day_sun_hour'),
                u'minute': mapping.get('day_sun_minute')
            })


class WeatherNodeNight(WeatherNode):
    def __init__(self, mapping):
        super(WeatherNodeNight, self).__init__()
        if mapping:
            self['sky'] = mapping.get('night_sky')
            self['temperature'] = mapping.get('night_temperature')
            self['wind_direction'] = mapping.get('night_wind_direction')
            self['wind_level'] = mapping.get('night_wind_level')
            self['sun'].update({
                u'type': mapping.get('night_sun_type'),
                u'hour': mapping.get('night_sun_hour'),
                u'minute': mapping.get('night_sun_minute')
            })


class WeatherNodeSugg(dict):
    def __init__(self, mapping):
        '''Return dict like:
            {
            'uv': {u'name': '', u'value': '', u'text': ''},
            }
        '''
        super(WeatherNodeSugg, self).__init__()
        if mapping:
            for key in mapping.keys():
                if key.startswith('sugg_') and key.endswith('_name'):
                    k = key[5:-5]
                    v = mapping[key]
                    self[k] = v


class WeatherLegacyOutput(dict):
    SUPPORT_FORECAST_DAYS = 14

    def __init__(self, today, city_query_obj, weather_records):
        super(WeatherLegacyOutput, self).__init__()

        self.city_query_obj = city_query_obj
        self.weather_records = weather_records
        # self.templating = templating
        self.today = today
        self.logger = logging.getLogger(self.__class__.__name__)

        # 3 parts: general/user/weather
        self['general'] = self._generate_general()
        self.logger.debug('>>> general: %s', self['general'])
        self['user'] = self._generate_user()
        self.logger.debug('>>> user: %s', self['user'])
        self['weather'] = self._generate_weather()
        self.logger.debug('>>> weather: %s', self['weather'])

    @time_calc_decorator()
    def _generate_general(self):
        '''Return {
        'place': {},
        'time': {},
        'target_time': {},
        'subfunction': {},
        'keywords': []
        }
        '''
        def _generate_keyword(keywords_list):
            _m = {
                u"温度": "temperature",
                u"气温": "temperature",
                u"雨":   "rain",
                u"伞":   "umbrella",
                u"pm2.5": "smog",
                u"雾霾": "smog",
                u"霾":   "smog",
                u"雪":   "snow",
                u"风":   "wind",
            }
            r = list()
            for keyword in keywords_list:
                eng_mapping = _m.get(keyword)
                if eng_mapping:
                    pair = {
                        u'std_tag': eng_mapping,
                        u'orig_word': keyword
                    }
                    r.append(pair)
            return r

        d = self.today.strftime('%Y-%m-%d')
        ds = datetime.strptime(d, '%Y-%m-%d')
        start_idx = (self.city_query_obj.date_in_datetime - ds).days
        self.logger.debug('date_in_datetime: %s',
                          self.city_query_obj.date_in_datetime)
        self.logger.debug('today: %s', self.today)
        obj = self.city_query_obj
        ret = {
            u'place': {
                u'city_name': obj.city_name,
                u'area': None,
                u'country': None
            },
            u'time': {
                u'weekday': self.today.weekday() + 1,
                u'date': self.today.strftime('%Y-%m-%d'),
                u'hour': self.today.hour,
                u'minute': self.today.minute
            },
            u'target_time': {
                u'start_weekday': obj.date_in_datetime.weekday() + 1,
                u'start_date': obj.date,
                u'duration': obj.duration,
                u'relative_idx': range(start_idx, start_idx + obj.duration),
                u'local_name': obj.time_name,
                u'forecast': WeatherLegacyOutput.SUPPORT_FORECAST_DAYS,
            },
            u'subfunction': None,
            u'keywords': _generate_keyword(obj.keywords)
        }
        self.logger.debug('ret: %s', ret)
        return ret

    def _generate_user(self):
        obj = self.city_query_obj
        return {
            u'name': None,
            u'language': None,
            u'gender': obj.gender,
            u'age': None,
            u'has': {
                u'car': None
            },
            u'preference': {
                u'suggest_outdoor': None,
                u'suggest_cloth': None,
                u'suggest_car': None,
                u'suggest_uv': None
            },
            u'usage_history': {
                u'last_uv_suggestion': None
            }
        }

    def _generate_weather(self):
        if not self.weather_records:
            return None

        today_str = self.today.strftime('%Y-%m-%d')
        today_rec = self.weather_records.get(today_str)

        tmpl = WeatherNodeFutureDays()
        for day in xrange(WeatherLegacyOutput.SUPPORT_FORECAST_DAYS):
            date = self.today + day * timedelta(days=1)
            date_str = date.strftime('%Y-%m-%d')
            record = self.weather_records.get(date_str)
            tmpl_oneday = WeatherNodeOneDay()
            if record:
                tmpl_oneday.update(record)
            else:
                self.logger.info('record(%s) is empty!!!', date_str)
            tmpl.add(tmpl_oneday)

        # self.logger.info(json.dumps(today_rec, indent=2, ensure_ascii=False))
        return {
            u'data': {
                u'today': {
                    u'now': WeatherNodeNow(today_rec),
                    u'day': WeatherNodeDay(today_rec),
                    u'night': WeatherNodeNight(today_rec),
                    u'suggestions': WeatherNodeSugg(today_rec),
                    u'alarms': []
                },
                u'future': {
                    u'week': tmpl
                },
                u'past': {
                    u'yesterday': {
                        u'day': WeatherNodeDay(None),
                        u'night': WeatherNodeNight(None)
                    },
                    u'week': None,
                    u'month': None
                },
            },
            u'insight': {
                u'trend': None,
                u'extreme': None
            }
        }


class WeatherService(object):
    def __init__(self, config):
        self.config = config
        self.dao = WeatherDao(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._city_nor_pattern = re.compile(ur"(省|市|市辖区|区|县|镇|乡)$",
                                            re.UNICODE)
        self._city_id_mapping = defaultdict(list)
        template_path = config.get('weather_template')
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_path),
            trim_blocks=True,
            lstrip_blocks=True,
            extensions=['jinja2.ext.do', ]
        )
        self.logger.info('config: %s', config)
        self.jinja_template = env.get_template('main.html')

        self._unit_test = False

    @property
    def city_id_mapping(self):
        if not self._city_id_mapping:
            for city in self.dao.city_list:
                self._city_id_mapping[city['city_name']].append(city)
        return self._city_id_mapping

    def _get_city_info(self, city_name):
        if not city_name:
            return None, city_name
        pairs = city_name.split(u',')
        for pair in reversed(pairs):
            normalize_pair = self._city_nor_pattern.sub('', pair)
            li = self.city_id_mapping[normalize_pair]
            if not li:
                continue

            # TODO(mike): deal with duplicated city here if need ?
            # TODO(mike): `东莞市市辖区` needs to be resolved to \
            #         `东莞市` or `东莞`, this is why we need this while loop.
            city_id = li[0]['city_id']

            if city_id == u'CN101080303':
                continue
            return city_id, normalize_pair
        return None, city_name

    @time_calc_decorator()
    def query(self, city_name=None, date=None, time_name=None, keywords=None,
              duration=1, gender=None, templating=True):
        '''Request weather infor of city_name

        :city_name: target city name in Simplified Chinese, the city_name might
        :type: unicode
        :date: target city name in Simplified Chinese
        :type: unicode
        :time_name: the time keyword use in templating
        :type: unicode
        :keywords: keyword like rain, snow, ...,etc
        :type: list
        :duration: requests number of days' weather
        :type: int
        :templating: apply jinja template or not
        :type: boolean

        :return: with templating: json dumped string with jinja template
        :rtype: unicode (json dump string)

        '''
        self.logger.debug('city_name: %s, date: %s, time_name: %s, '
                          'keywords: %s, duration: %s, gender: %s',
                          city_name, date, time_name, keywords,
                          duration, gender)
        # Get data by date
        today = datetime.today()
        if date is None:
            date = today.strftime('%Y%m%d')
        city_id, normalize_city_name = self._get_city_info(city_name)
        city_q_obj = CityQuery(city_id, normalize_city_name, date, time_name,
                               keywords, gender, duration)
        self.logger.debug('city_q_obj; %s', city_q_obj)

        # TODO(mike): handle city_id is None case
        if not city_q_obj.city_id:
            output = WeatherLegacyOutput(today, city_q_obj, dict())
        else:
            weather_records = self.dao.get_records(city_q_obj.city_id)
            self.logger.info('weather_records keys: %s', weather_records.keys())

            # unit-test, make today record be empty
            if self._unit_test:
                n = dict()
                for k, v in weather_records.iteritems():
                    date_k = datetime.strptime(k, '%Y-%m-%d')
                    date_k_1 = date_k + timedelta(days=1)
                    n[date_k_1.strftime('%Y-%m-%d')] = v
                weather_records = n

            output = None
            try:
                output = WeatherLegacyOutput(today, city_q_obj, weather_records)
            except:
                self.logger.exception('')
                raise
        self.logger.debug('output: %s', output)

        @time_calc_decorator()
        def apply_template(obj_template, output):
            return obj_template.render(output)

        # self.logger.debug(json.dumps(output, indent=2, ensure_ascii=False))
        if templating:
            return apply_template(self.jinja_template, output)
        return output


#if __name__ == '__main__':
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
#
#    server_url = 'https://content-sh.emotibot.com'
#    api_key = u'2WDGS5SCH68RWDLC76BI9J6CZEKJM5QM'
#    update_interval = 60
#    config = {
#        'server_url': 'https://content-sh.emotibot.com',
#        'api_key': u'2WDGS5SCH68RWDLC76BI9J6CZEKJM5QM',
#        'weather_template': os.path.join(os.path.dirname(__file__),
#                                         'templates/weather')
#    }
#    service = WeatherService(config)
#    today = datetime.today()
#
#    # ===== Basic Testing =====
#    def basic_test(city_name, date, time_name=None, duration=1, keywords=None):
#        print service.query(city_name, date=date, time_name=time_name,
#                            duration=duration, keywords=keywords)
#    # 1. 上海今天天氣
#    basic_test(u'上海', today.strftime('%Y%m%d'), time_name=u'今天')
#    # 2. 北京周末天氣
#    date = today.strftime('%Y%m%d')
#    weekday = today.weekday()
#    if weekday < 5:
#        date = (today + timedelta(days=(5-weekday))).strftime('%Y%m%d')
#    basic_test(u'上海', date, duration=2, time_name=u'周末')
#    # 3. 廣州明天天氣
#    basic_test(u'广州', (today + timedelta(days=1)).strftime('%Y%m%d'),
#               time_name=u'明天')
#    # 4. 重慶下周五天氣
#    basic_test(u'重庆',
#               (today + timedelta(days=(4-weekday+7))).strftime('%Y%m%d'),
#               time_name=u'下周五')
#    # 5. 台北明天會下雨嗎
#    basic_test(u'台北', (today + timedelta(days=1)).strftime('%Y%m%d'),
#               time_name=u'明天', keywords=[u'雨'])
#    # 6. 武汉明天空气好吗
#    basic_test(u'武汉', (today + timedelta(days=1)).strftime('%Y%m%d'),
#               time_name=u'明天', keywords=[u'霾'])
#    # 7. 海南天氣
#    print service.query(u'海南', today.strftime('%Y%m%d'))
#    # 8. 台中昨天天气
#    basic_test(u'台中', (today + timedelta(days=-1)).strftime('%Y%m%d'),
#               time_name=u'昨天')
#    # ===== Random test =====
#    # city_names = [u'上海', u'北京', u'台北', u'海南', u'广州']
#    # # for city_name in city_names:
#    # #     print service.query(city_name)
#    # keywords = [u'温度', u'气温', u'雨', u'伞', u'pm2.5', u'雾霾', u'霾',
#    #             u'雪', u'风']
#    # time_names = [u'明天', u'后天', u'5月15号', u'今天', u'下周一']
#    # dates = [u'20170101', u'20171231', today.strftime('%Y%m%d'),
#    #          (today + timedelta(days=1)).strftime('%Y%m%d'),
#    #          (today + timedelta(days=7)).strftime('%Y%m%d')]
#    # keywords = [u'雨']
#    # durations = [1, 2, 3, 4, 5]
#
#    # for n in range(5):
#    #     city_name = city_names.pop(randint(0, len(city_names)-1))
#    #     time_name = time_names.pop(randint(0, len(time_names)-1))
#    #     date = dates.pop(randint(0, len(dates)-1))
#    #     duration = durations.pop(randint(0, len(durations)-1))
#    #     print service.query(city_name, time_name=time_name, date=date,
#    #                         duration=duration)
