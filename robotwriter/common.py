import time
import logging


logger = logging.getLogger(__name__)


def time_calc_decorator(datadog_statsd=None):
    def real_time_calc_decorator(func):
        def wrapper(obj, *args, **kwargs):
            _logger = getattr(obj, 'logger', logger)
            _logger.info('[IN] %s:%s', obj.__class__.__name__, func.__name__)
            t_p = time.time()
            try:
                if datadog_statsd:
                    datadog_statsd.increment('query.count')
                    with datadog_statsd.timed('query.response.time'):
                        return func(obj, *args, **kwargs)
                return func(obj, *args, **kwargs)
            finally:
                _logger.info('[OUT] %s:%s(%s, %s): cost: %s',
                             obj.__class__.__name__, func.__name__, args,
                             kwargs, time.time() - t_p)
        return wrapper
    return real_time_calc_decorator
