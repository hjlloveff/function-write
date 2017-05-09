import time
import logging


logger = logging.getLogger(__name__)


def time_calc_decorator(func):
    def wrapper(obj, *args, **kwargs):
        _logger = getattr(obj, 'logger', logger)
        t_p = time.time()
        try:
            return func(obj, *args, **kwargs)
        finally:
            _logger.info('%s: cost: %s', func.__name__, time.time() - t_p)
    return wrapper
