# -*- coding: utf-8 -*-
import time


class DictCache(object):
    def __init__(self, expiration=30*60):
        self.expiration = expiration
        self.cache = dict()

    def get(self, k):
        v = self.cache.get(k)
        if v and time.time() < v['expiration']:
            return v['data']
        return None

    def update(self, k, v):
        v_ = {
            'data': v,
            'expiration': time.time() + self.expiration
        }

        self.cache[k] = v_


if __name__ == '__main__':
    cache = DictCache(expiration=5)
    cache.update('a', 5)
    print cache.get('a')
    time.sleep(5)
    print cache.get('a')
