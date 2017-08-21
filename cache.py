# -*- coding: utf-8 -*-
import time
from collections import OrderedDict


class DictCache(object):
    def __init__(self, expiration=30*60, size=1000):
        assert isinstance(expiration, int)
        assert isinstance(size, int) and size > 0

        self.expiration = expiration
        self.cache = OrderedDict()
        self.size = size

    def __str__(self):
        return u'\n'.join('%s: %s' % (k, v) for k, v in vars(self).iteritems())

    def __len__(self):
        return len(self.cache)

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

        # deal cache full case
        if len(self.cache) > self.size:
            try:
                # remove first insert item
                self.cache.popitem(last=False)
            except:
                pass


if __name__ == '__main__':
    cache = DictCache(expiration=5, size=5)
    cache.update('1', u'上海')
    cache.update('2', 'b')
    cache.update('3', u'北京')
    cache.update('4', None)
    cache.update('5', 'e')
    cache.update('6', 'f')
    assert len(cache) == 5
    print cache
