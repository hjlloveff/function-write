# Web App Templates

This is a `sample` Python Web app project.
This project includes:

* use `Python2.7`
* build RESTful API with [flask](http://flask.pocoo.org/)
* run service with `gunicorn`
* build docker image

## Code Structure

## Layout

this is the inteneded layout of this project:

        entrypoint.sh
        server.py
        cache.py
        constants.py
            $module/controller.py
            $module/service.py
            $module/dao.py

the function of top-level files and module are described as follows:

* server.py
    * get `environment variable` and create config data (i.e., a dictionary)
    * create flask API server
    * bind endpoint and request by `setup_route` implemented by each `module`
* cache.py
    * leverage Redis to implement data cache

* constants.py
    * define common constants to avoid handy string typo error
* $module
    * implement functional module
    * the convention will be separate implementation into:
        * controller.py: receive request, send response, do request data validation, export `controller.setup_route` function to `server.py`
        * service.py: implement service layer for integration with other module.
        * dao.py: implement data access function.

## Real Sample

        server.py: entry point class
        cache.py
            news/controller.py
            news/service.py
            news/dao.py

## Develop Guidelines

* please make sure `$module/dao.py` only accessed by code in `same $module`.
* for cross module data access, please use `service` instead. please check the example listed below:

`Not Good`

        # in search module
        from news.dao import NewsDAO

        def get_news_from_google(keyword):
            newsDAO = NewsDAO(self.config) // bad, really bad

`Good`

        # in search module
        from news.service import NewsService

        def get_news_from_google(keyword):
            newsService = NewsService(self.config) // great, you didn't break the rule

* please implement caching in `controller`, not in `service` or `dao`. this will make unit-testing easier and reasonable.
* you should have questions about - what's the difference between service and dao?
    * answer: `dao` need to `focus on data access`, nothing else. if we are going to do `data transformation, integration and other things`, we `must do it in service`. service is `intended to exported to other moudles`, and that means we need to `do input check and validation in service`.

### Request Processing Flows

                 |
                 | (request)
                 |
                 V
            +==========+     +===========+     +===================+  (route)   +======================+
            | gunicorn | --> | server.py | --> | flask api server  | ----+----> |handler1 from moduleA |
            +==========+     +===========+     +===================+     |      +======================+
                                                                         |      +======================+
                                                                         +----> |handler2 from moduleB |
                                                                                +======================+

### Testing

you can issue command:

`unit test`:

        nosetests -v tests/news_test.py

`web api integration test`:

        nosetests -v tests/api_test.py

## Production

* please change `entrypoint.sh` to tune parameters of gunicorn:
    * --workers: number of worker process, or even use setting in enviroment variable, default `1`.
    * --timeout: timeout for worker process to kill/restart, default `30`.
    * --limit-request-field\_size: max request body size, default `8k`.
    * --bind: address to bind, default `127.0.0.1:8000`.
    * --max-requests: maximum number of requests that worker process will restart, default `0` (never).

### Tuning

* if you would like to boost the performance of your python application, the options are as follows:
    * use `pypy`. usually, pypy is 20% ~ 100% faster than cpython. however, pypy use more memory, and you need to do GC tuning carefull.
    * profile your application with `profile` and file bottlenecks.

## Benchmark

### Environment

* Host: MBP 15", 16 GB Memory
* OS: Mac OS X

### Endpoint

* /news/
    * cache on Redis with expiration `60` seconds, query database if cache missed.

### Detail

* gunicorn + 1 worker process

        Concurrency Level:      50
        Time taken for tests:   0.160 seconds
        Complete requests:      200
        Failed requests:        0
        Total transferred:      34600 bytes
        HTML transferred:       3200 bytes
        Requests per second:    1252.50 [#/sec] (mean)
        Time per request:       39.920 [ms] (mean)
        Time per request:       0.798 [ms] (mean, across all concurrent requests)
        Transfer rate:          211.60 [Kbytes/sec] received

        Connection Times (ms)
                      min  mean[+/-sd] median   max
        Connect:        0    0   0.4      0       1
        Processing:     1   35  10.4     37      45
        Waiting:        1   35  10.4     37      45
        Total:          2   35  10.1     37      46

        Percentage of the requests served within a certain time (ms)
          50%     37
          66%     41
          75%     44
          80%     44
          90%     45
          95%     45
          98%     45
          99%     45
         100%     46 (longest request)


* gunicorn + 5 worker process

          Concurrency Level:      50
          Time taken for tests:   0.054 seconds
          Complete requests:      200
          Failed requests:        0
          Total transferred:      34600 bytes
          HTML transferred:       3200 bytes
          Requests per second:    3709.06 [#/sec] (mean)
          Time per request:       13.480 [ms] (mean)
          Time per request:       0.270 [ms] (mean, across all concurrent requests)
          Transfer rate:          626.63 [Kbytes/sec] received

          Connection Times (ms)
                        min  mean[+/-sd] median   max
          Connect:        0    1   0.6      0       2
          Processing:     2   11   3.3     12      16
          Waiting:        1   11   3.3     12      16
          Total:          4   12   2.8     12      16
          WARNING: The median and mean for the initial connection time are not within a normal deviation
                  These results are probably not that reliable.

          Percentage of the requests served within a certain time (ms)
            50%     12
            66%     13
            75%     14
            80%     15
            90%     15
            95%     16
            98%     16
            99%     16
           100%     16 (longest request)


* gunicorn + 10 worker process

          Concurrency Level:      20
          Time taken for tests:   0.045 seconds
          Complete requests:      200
          Failed requests:        0
          Total transferred:      34600 bytes
          HTML transferred:       3200 bytes
          Requests per second:    4462.39 [#/sec] (mean)
          Time per request:       4.482 [ms] (mean)
          Time per request:       0.224 [ms] (mean, across all concurrent requests)
          Transfer rate:          753.90 [Kbytes/sec] received

          Connection Times (ms)
                        min  mean[+/-sd] median   max
          Connect:        0    1   0.7      1       5
          Processing:     2    3   1.1      3       8
          Waiting:        2    3   1.1      3       8
          Total:          2    4   1.3      4       9

          Percentage of the requests served within a certain time (ms)
            50%      4
            66%      4
            75%      5
            80%      5
            90%      6
            95%      8
            98%      8
            99%      9
           100%      9 (longest request)