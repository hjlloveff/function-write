# -*- coding: utf-8 -*-
import os
import json
import time
from datetime import datetime, timedelta

import pytest

from robotwriter.dao import WeatherDao
from robotwriter.weather_service import CityQuery
from robotwriter.service import WeatherService, SoccerService, TimeInfoService
from robotwriter.exception import NotFoundError


obj_wther_dao = None
obj_wther_srv = None
obj_soccer_srv = None
obj_timeinfo_srv = None


@pytest.fixture(scope='session')
def city_id_notfound():
    return u'CN101010999'


@pytest.fixture(scope='session')
def wther_config():
    return {
        'server_url': 'https://content-sh.emotibot.com',
        'api_key': '2WDGS5SCH68RWDLC76BI9J6CZEKJM5QM',
        'weather_template': os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                         'robotwriter/templates/weather')
    }


@pytest.fixture(scope='session')
def soccer_config():
    return {
        'server_url': 'https://content-sh.emotibot.com',
        'api_key': '2WDGS5SCH68RWDLC76BI9J6CZEKJM5QM',
        'soccer_template': os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                        'robotwriter/templates/soccer')
    }


@pytest.fixture(scope='session')
def timeinfo_config():
    return {
        'server_url': 'https://content-sh.emotibot.com',
        'api_key': '2WDGS5SCH68RWDLC76BI9J6CZEKJM5QM',
        'timeinfo_template': os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                        'robotwriter/templates/timeinfo')
    }


@pytest.fixture(scope='session')
def city_list():
    '''
    mapping = {
        u'CN101071201': u'辽宁',
        u'CN101010100': u'北京',
        u'CN101060110': u'吉林'
    }
    '''
    return [
        {u'city_id': u'CN101071201', u'city_name': u'辽宁'},
        {u'city_id': u'CN101010100', u'city_name': u'北京'},
        {u'city_id': u'CN101060110', u'city_name': u'吉林'}
    ]


@pytest.fixture(scope='session')
def wther_dao(wther_config, city_list):
    global obj_wther_dao

    if obj_wther_dao is None:
        obj_wther_dao = WeatherDao(wther_config, city_list=city_list)
        # obj_wther_dao.start()
    return obj_wther_dao


@pytest.fixture(scope='session')
def wther_service(wther_config):
    global obj_wther_srv

    if obj_wther_srv is None:
        obj_wther_srv = WeatherService(wther_config)
    return obj_wther_srv


@pytest.fixture(scope='session')
def soccer_service(soccer_config):
    global obj_soccer_srv

    if obj_soccer_srv is None:
        obj_soccer_srv = SoccerService(soccer_config)
    return obj_soccer_srv


@pytest.fixture(scope='session')
def timeinfo_service(timeinfo_config):
    global obj_timeinfo_srv

    if obj_timeinfo_srv is None:
        obj_timeinfo_srv = TimeInfoService(timeinfo_config)
    return obj_timeinfo_srv


@pytest.fixture(scope='session', params=[u'上海', u'北京', u'广州'])
def city_name(request):
    return request.param


@pytest.fixture(scope='session', params=[u'md', u'mdw', u'HM'])
def timeinfo_type(request):
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
    def test_get_city_list(self, wther_config):
        dao = WeatherDao(wther_config)
        city_list = dao.city_list
        assert isinstance(city_list, list)
        assert len(city_list) > 2500
        for city in city_list:
            # print city.city_id, city.city_name
            assert city['city_id']
            assert city['city_name']
        # self._city_list = city_list

    def test_get_city_weather_notfound(self, wther_dao, city_id_notfound):
        with pytest.raises(NotFoundError):
            wther_dao._get_city_weather(city_id_notfound)

    def test_get_city_weather_all(self, wther_dao):
        time.sleep(10)
        assert len(wther_dao.weather_cache) == 3

    def test_get_records(self, wther_dao):
        wther_dao.get_records(u'CN101010100')
        # from cache, length will not increase
        assert len(wther_dao.weather_cache) == 3

        wther_dao.get_records(u'CN101010200')
        assert len(wther_dao.weather_cache) == 4


class TestWeatherService(object):

    def test_today_weather(self, wther_service):
        city_name = u'北京'
        date = datetime.today().strftime('%Y%m%d')
        time_name = u'今天'
        ret = wther_service.query(city_name, date, time_name=time_name)
        assert len(ret.split(',')) == 2

    def test_today_weather_no_data(self, wther_service):
        wther_service._unit_test = True
        try:
            city_name = u'武汉'
            date = datetime.today().strftime('%Y%m%d')
            time_name = u'今天'
            ret = wther_service.query(city_name, date, time_name=time_name)
            assert u'小影暂时没有找到你想要的地方的天气资讯，哭哭' in ret
        finally:
            wther_service._unit_test = False

    def test_city_not_supported(self, wther_service):
        city_name = u'海南'
        ret = wther_service.query(city_name)
        assert u'暂时没有提供' in ret

    def test_yesterday(self, wther_service):
        city_name = u'北京'
        date = datetime.today() + timedelta(days=-1)
        ret = wther_service.query(city_name, date.strftime('%Y%m%d'))
        assert u'暂时' in ret

    def test_today_weather_no_city_name(self, wther_service):
        ret = wther_service.query()
        assert u'在句子中加上地点再问小影一次吧~' in ret


class TestSoccerService(object):
    def test_normal_case(self, soccer_service):
        team = u'利物浦'
        soccer_service.query(dict(team1=team, type=u'match'))

    def test_team_not_found(self, soccer_service):
        team = u'纳放'
        ret = soccer_service.query(dict(team1=team, type=u'match'))
        assert u'球队在这段时间好像没有比赛哦' in ret.decode('utf-8')


class TestTimeInfoService(object):
    def test_normal_case(self, timeinfo_service, timeinfo_type):
        today = datetime.today()
        today_str = today.strftime('%Y%m%d')
        timeinfo_service.query(today_str, timeinfo_type)


    #def test_get_city_name2id(self, wther_dao):
    #    city_name = u'北京'
    #    city_id = u'CN101010100'
    #    assert wther_dao._get_city_id(city_name) == [city_id]

    #    city_name = u'朝阳'
    #    mapping = {
    #        u'CN101071201': u'辽宁',
    #        u'CN101010300': u'北京',
    #        u'CN101060110': u'吉林'
    #    }
    #    for k, v in mapping.iteritems():
    #        r = wther_dao._get_city_id(city_name, province=v)
    #        assert r and r[0] == k

    #    l = wther_dao._get_city_id(city_name)
    #    assert len(l) == 3

    #def test_get_city_weather(self, wther_dao, city_id_notfound):
    #    ret = wther_dao.get_weather(city_id_notfound)
    #    assert isinstance(ret, list) & len(ret) == 0

    #    time.sleep(5)
    #    city_name = u'朝阳'
    #    ret = wther_dao.get_weather(city_name)
    #    # print json.dumps(ret, indent=2, ensure_ascii=False)
    #    assert isinstance(ret, list) and len(ret) == 3

    #    province = u'辽宁'
    #    ret = wther_dao.get_weather(city_name, province=province)
    #    assert isinstance(ret, list) and len(ret) == 1 and len(ret[0]) >= 14, [n['date'] for n in ret[0]]

    #    error_list = list()
    #    # print json.dumps(wther_dao.city_weather.values(), indent=2, ensure_ascii=False)
    #    for city in wther_dao.city_list[:10]:
    #        ret = wther_dao.get_weather(city.city_name)
    #        for r in ret:
    #            if len(r) < 14:
    #                error_list.append(r)

    #    if error_list:
    #        assert False, ['%s: %s' % (len(n), n['city_name']) for n in error_list]


#class TestTemplate(object):
#    def test_today_template(self, city_q_obj, weather_data, date_today):
#        d = TemplateToday(city_q_obj, weather_data, date_today)
#        assert False, json.dumps(d, indent=2)
