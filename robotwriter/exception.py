import sys
import traceback


class Error(Exception):
    def __init__(self, msg, *args, **kwargs):
        super(Error, self).__init__(msg, *args, **kwargs)
        self._tb = sys.exc_info()[0]  # might be None or exc_info

    def __str__(self):
        super_str = super(Error, self).__str__()
        if self._tb:
            tb = u''.join(traceback.format_exception(*self._tb))
            return '%s caused by %s' % (super_str, tb)
        return super_str


class ServiceError(Error):
    pass


class NotFoundError(Error):
    pass
