# -*- coding: utf-8 -*-

import redis
import constants

# internal connection pool
_REDIS_POOL = None

# cache object
class Cache(object):
    """
        cache storage class
    """
    def __init__(self, config):
        self.config = config
        self.init_pool(config)

    def get(self, key):
        """
            get value on cache server with given key -> string
        """
        if key is None:
            return None

        ret = None
        conn = None
        try:
            conn = self.get_conn()
            if conn:
                ret = conn.get(key)
        except Exception as e:
            pass

        if isinstance(ret, bytes):
            ret = ret.decode('utf-8')

        return ret

    def set(self, key, value, expire):
        """
            set value on cache server with given key and value -> bool
        """
        if key is None or \
            value is None:
            return False

        ret = False
        conn = None
        try:
            conn = self.get_conn()
            if conn:
                ret = conn.set(key, value, ex=expire)
        except Exception as e:
            pass

        return ret
            

    def get_conn(self):
        """
            get cache connection
        """
        global _REDIS_POOL

        ret = None
        if _REDIS_POOL is not None:
            ret = redis.Redis(
                connection_pool=_REDIS_POOL,
                decode_responses=True
            )

        return ret

    def init_pool(self, config):
        """
            initialize connection pool
        """
        global _REDIS_POOL

        if _REDIS_POOL is not None:
            return

        host_str = config.get(
            constants.CFG_REDIS_SERVER,
            constants.REDIS_SERVER_DEFAULT
        )
        redis_db = config.get(
            constants.CFG_REDIS_DB,
            constants.REDIS_DB_DEFAULT
        )

        (redis_server, redis_port) = self.parse_host_port(host_str)
        try:
            _REDIS_POOL = redis.ConnectionPool(
                host=redis_server,
                port=redis_port,
                db=redis_db
            )
        except Exception as e:
            pass

        return

    def parse_host_port(self, host_str):
        """
            prase redis server string (e.g., 127.0.0.1:6379) -> string, int
        """
        ret = constants.REDIS_SERVER_DEFAULT
        retPort = constants.REDIS_PORT_DEFAULT
        idx = host_str.find(':')

        if -1 != idx:
            tmp = host_str[idx+1:]
            ret = host_str[0:idx]

            if tmp.isdigit():
                retPort = int(tmp)

        return (ret, retPort)
