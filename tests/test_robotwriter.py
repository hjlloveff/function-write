# -*- coding: utf-8 -*-
import json
import time
from datetime import datetime

import pytest

from robotwriter.dao import WeatherDao
from robotwriter.service import CityQuery
from robotwriter.template import TemplateToday


obj_wther_dao = None
obj_wther_srv = None


@pytest.fixture(scope='session')
def city_id_notfound():
    return u'CN101010999'


@pytest.fixture(scope='session')
def wther_config():
    return {
        'content_url': 'https://content-sh.emotibot.com',
        'content_api_key': '2WDGS5SCH68RWDLC76BI9J6CZEKJM5QM'
    }


@pytest.fixture(scope='session')
def wther_dao(wther_config):
    global obj_wther_dao

    if obj_wther_dao is None:
        obj_wther_dao = WeatherDao(wther_config)
        obj_wther_dao.start()
    return obj_wther_dao


#@pytest.fixture(scope='session')
#def wther_srv(wther_dao):
#    global obj_wther_srv


@pytest.fixture(scope='session', params=[u'上海', u'北京', u'广州'])
def city_name(request):
    return request.param


@pytest.fixture(scope='session')
def date_today():
    return datetime.today()

@pytest.fixture(scope='session')
def date_today_str(date_today):
    return date_today.strftime('%Y-%m-%d')


@pytest.fixture(scope='session', params=[u'今天', u''])
def time_name(request):
    return request.param


@pytest.fixture(scope='session', params=[u'雨', u'雪', u'霾', u''])
def keywords(request):
    return [request.param]


@pytest.fixture(scope='session', params=[u'女', u'男'])
def gender(request):
    return request.param


@pytest.fixture(scope='session')
def city_q_obj(city_name, date_today_str, time_name, keywords, gender):
    d = CityQuery(city_name, date_today_str, time_name, keywords, gender)
    print type(d)
    return d


@pytest.fixture(scope='session')
def weather_data(wther_dao, city_name):
    return wther_dao.get_weather(city_name)[0]
    # do not handle duplicated city_name here


class TestWeatherDao(object):
    # def __init__(self, *args, **kwargs):
    #     super(TestWeatherDao, self).__init__(*args, **kwargs)
    #     self._city_list = None

    def test_get_city_list(self, wther_dao):
        city_list = wther_dao.city_list
        assert isinstance(city_list, list)
        assert len(city_list) > 2500
        for city in city_list:
            # print city.city_id, city.city_name
            assert city.city_id
            assert city.city_name
        # self._city_list = city_list

    def test_get_city_name2id(self, wther_dao):
        city_name = u'北京'
        city_id = u'CN101010100'
        assert wther_dao._get_city_id(city_name) == [city_id]

        city_name = u'朝阳'
        mapping = {
            u'CN101071201': u'辽宁',
            u'CN101010300': u'北京',
            u'CN101060110': u'吉林'
        }
        for k, v in mapping.iteritems():
            r = wther_dao._get_city_id(city_name, province=v)
            assert r and r[0] == k

        l = wther_dao._get_city_id(city_name)
        assert len(l) == 3

    def test_get_city_weather(self, wther_dao, city_id_notfound):
        ret = wther_dao.get_weather(city_id_notfound)
        assert isinstance(ret, list) & len(ret) == 0

        time.sleep(5)
        city_name = u'朝阳'
        ret = wther_dao.get_weather(city_name)
        # print json.dumps(ret, indent=2, ensure_ascii=False)
        assert isinstance(ret, list) and len(ret) == 3

        province = u'辽宁'
        ret = wther_dao.get_weather(city_name, province=province)
        assert isinstance(ret, list) and len(ret) == 1 and len(ret[0]) >= 14, [n['date'] for n in ret[0]]

        error_list = list()
        # print json.dumps(wther_dao.city_weather.values(), indent=2, ensure_ascii=False)
        for city in wther_dao.city_list[:10]:
            ret = wther_dao.get_weather(city.city_name)
            for r in ret:
                if len(r) < 14:
                    error_list.append(r)

        if error_list:
            assert False, ['%s: %s' % (len(n), n['city_name']) for n in error_list]


class TestTemplate(object):
    def test_today_template(self, city_q_obj, weather_data, date_today):
        d = TemplateToday(city_q_obj, weather_data, date_today)
        assert False, json.dumps(d, indent=2)
