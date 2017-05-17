# -*- coding: utf-8 -*-
import logging
import json

from flask import Flask
from flask import Response
from flask_restful import Resource, reqparse
from datadog import statsd

import constants
from cache import DictCache
from .exception import ServiceError, ClientError
from .service import WeatherService, SoccerService, TimeInfoService
from .common import time_calc_decorator


# configure datadog statsd
statsd.host = constants.DATADOG_HOST
statsd.port = constants.DATADOG_PORT
statsd.namespace = constants.DATADOG_NAMESPACE
statsd.constant_tags = constants.DATADOG_TAGS
statsd.use_ms = constants.DATADOG_USE_MS


def _weather_parser():
    parser = reqparse.RequestParser()
    parser.add_argument('date', type=str)
    parser.add_argument('time_name')
    parser.add_argument('keywords', action='append')
    parser.add_argument('gender')
    parser.add_argument('days', type=int)
    parser.add_argument('city_name', required=True)
    return parser


def _soccer_parser():
    parser = reqparse.RequestParser()
    parser.add_argument('type', type=str, default='match')
    parser.add_argument('team1', required=True)
    parser.add_argument('team2')
    parser.add_argument('match_id', type=str)
    parser.add_argument('league_type_name')
    parser.add_argument('time_from', type=str)
    parser.add_argument('time_to', type=str)
    parser.add_argument('time_name')
    return parser


def _timeinfo_parser():
    parser = reqparse.RequestParser()
    parser.add_argument('date', type=str, required=True)
    parser.add_argument('type', type=str, required=True)
    parser.add_argument('time_name')
    parser.add_argument('lunar', type=str)
    parser.add_argument('festival')
    return parser


def setup_route(config, api):
    '''route function to handle restful api

    / usage
    /(weather|soccer|timeinfo) - without templating
    /(weather|soccer|timeinfo)/human
    /(weather|soccer|timeinfo)/debug_json
    /(weather|soccer|timeinfo)/debug_story
    /V2/(weather|soccer|timeinfo) - with templating
    '''
    WeatherV2Handler.config = config
    WeatherV2Handler.service = WeatherService(config)
    WeatherV2Handler.parser = _weather_parser()
    WeatherV2Handler.cache = DictCache()

    TimeInfoV2Handler.config = config
    TimeInfoV2Handler.service = TimeInfoService(config)
    TimeInfoV2Handler.parser = _timeinfo_parser()
    TimeInfoV2Handler.cache = DictCache()

    SoccerV2Handler.config = config
    SoccerV2Handler.service = SoccerService(config)
    SoccerV2Handler.parser = _soccer_parser()
    SoccerV2Handler.cache = DictCache()

    api.add_resource(WeatherV2Handler, '/V2/weather')
    api.add_resource(TimeInfoV2Handler, '/V2/timeinfo', '/timeinfo')
    api.add_resource(SoccerV2Handler, '/V2/soccer', '/soccer')


class SoccerV2Handler(Resource):
    config = None
    service = None
    parser = None
    cache = None

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        super(SoccerV2Handler, self).__init__()

    @time_calc_decorator(statsd)
    def get(self):
        args = SoccerV2Handler.parser.parse_args()
        self.logger.info('args(%s): %s', type(args), args)
        resp = Response()
        cache_key = u''.join(unicode(v) if not isinstance(v, unicode) else v for v in args.values())
        cache = SoccerV2Handler.cache.get(cache_key)
        # self.logger.info('cache: %s, cache_key: %s', cache, cache_key)
        if cache:
            resp.data = cache
            self.logger.info('cache hit(%s)', cache_key)
        else:
            answer = None
            self.logger.info('cache miss(%s)', cache_key)
            try:
                resp.data = SoccerV2Handler.service.query(args)
                SoccerV2Handler.cache.update(cache_key, resp.data)
            except ServiceError as exp:
                status_code = 503
                answer = exp
            except ClientError as exp:
                status_code = 400
                answer = exp
            except Exception as exp:
                status_code = 500
                answer = exp

            if answer:
                resp.data = json.dumps({
                    'answer': answer,
                    'statusCode': status_code
                })
        return resp


class WeatherV2Handler(Resource):
    config = None
    service = None
    parser = None
    cache = None

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        super(WeatherV2Handler, self).__init__()

    @time_calc_decorator(statsd)
    def get(self):
        args = WeatherV2Handler.parser.parse_args()
        self.logger.info('%s', args)
        cache_key = u''.join(unicode(v) if not isinstance(v, unicode) else v for v in args.values())
        cache = WeatherV2Handler.cache.get(cache_key)
        resp = Response()
        if cache:
            resp.data = cache
            self.logger.info('cache hit(%s)', cache_key)
        else:
            self.logger.info('cache miss(%s)', cache_key)
            try:
                answer = WeatherV2Handler.service.query(
                    args['city_name'],
                    date=args['date'],
                    time_name=args['time_name'],
                    keywords=args['keywords'],
                    gender=args['gender'],
                    duration=args['days'],
                    templating=True)
                data = json.dumps({
                    'answer': answer,
                    'statusCode': 200
                })
                resp.data = data
                WeatherV2Handler.cache.update(cache_key, resp.data)
            except Exception as exp:
                self.logger.exception('')
                resp.data = {
                    'answer': exp,
                    'statusCode': 500
                }
        return resp


class TimeInfoV2Handler(Resource):
    config = None
    service = None
    parser = None
    cache = None

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        super(TimeInfoV2Handler, self).__init__()

    @time_calc_decorator(statsd)
    def get(self):
        args = TimeInfoV2Handler.parser.parse_args()
        self.logger.info('args(%s)', args)
        resp = Response()
        cache_key = u''.join(unicode(v) if not isinstance(v, unicode) else v for v in args.values())
        cache = TimeInfoV2Handler.cache.get(cache_key)
        if cache:
            self.logger.info('cache hit(%s)', cache_key)
        else:
            self.logger.info('cache miss(%s)', cache_key)
            try:
                resp.data = TimeInfoV2Handler.service.query(
                    args['date'],
                    args['type'],
                    time_name=args['time_name'],
                    lunar_date=args['lunar'],
                    festival=args['festival']
                )
                TimeInfoV2Handler.cache.update(cache_key, resp.data)
            except Exception as exp:
                resp.data = exp
                resp.status = 500
        return resp

