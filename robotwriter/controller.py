# -*- coding: utf-8 -*-
import logging
import json

from flask import Flask
from flask import Response
from flask_restful import Resource, reqparse

from .service import WeatherService, SoccerService, TimeInfoService


def _weather_parser():
    parser = reqparse.RequestParser()
    parser.add_argument('date', type=str)
    parser.add_argument('time_name', type=str)
    # parser.add_argument('today', type=str)
    parser.add_argument('keywords', action='append')
    # parser.add_argument('subfunction')
    parser.add_argument('gender', type=str)
    parser.add_argument('duration', type=int)
    # parser.add_argument('city_key', type=str)
    # parser.add_argument('city_val', type=str)
    parser.add_argument('city_name', type=str, required=True)
    return reqparse


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
    api.add_resource(WeatherV2Handler, '/V2/weather')


class WeatherV2Handler(Resource):
    config = None
    service = None
    parser = None
    cache = None

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        super(WeatherV2Handler, self).__init__()

    def get(self, source):
        args = WeatherV2Handler.parser.parse_args()
        self._logger.info('%s', args)
        cache = WeatherV2Handler.cache.get(args.city)
        resp = Response()
        if cache and not cache.expired:
            resp.data = cache.data
        else:
            resp.data = WeatherV2Handler.service.query(
                args.city_name,
                date=args.date,
                time_name=args.time_name,
                keywords=args.keywords,
                gender=args.gender,
                duration=args.duration,
                templating=True)
            # TODO(mike): handle wrong resp.data
            WeatherV2Handler.cache[args.city] = resp.data
        return resp
