'''Httpclient function
'''
import time
import logging
import json

from requests import Session, Request
from requests.exceptions import (ConnectionError, SSLError, Timeout,
                                 ChunkedEncodingError)

from .exception import ServiceError


LOG = logging.getLogger(__name__)


# If need method other than GET, need to implment as a class to
# deal with all HTTP Method like POST, PATCH, DELETE...
def do_get_request(url, headers=None, params=None, retry=5):
    '''Request GET function
    '''
    err = None
    for retry_count in xrange(retry):
        try:
            sess = Session()
            req = Request('GET', url, headers=headers, params=params)
            args = []
            if headers:
                args.append('headers=%s' % json.dumps(headers))
            if params:
                args.append('params=%s' % json.dumps(params))
            LOG.debug('GET %s %s', url, args)
            resp = sess.send(req.prepare(), verify=False, timeout=(60, 60))
            if 500 <= resp.status_code < 600:
                raise ServiceError(resp)
            return resp
        except (ConnectionError, SSLError, Timeout,
                ChunkedEncodingError) as exp:
            err = ServiceError(exp)
            LOG.debug('%s, backoff retry, sleep %s sec', exp,
                      (2 ** retry_count))
            time.sleep(2 ** retry_count)
        except ServiceError as exp:
            err = exp
            LOG.debug('%s, backoff retry, sleep %s sec', exp,
                      (2 ** retry_count))
            time.sleep(2 ** retry_count)
    if err:
        raise err
