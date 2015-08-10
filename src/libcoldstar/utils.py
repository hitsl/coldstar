# -*- coding: utf-8 -*-
import datetime
import json
import functools
from Queue import Queue

from twisted.internet import defer
from libcoldstar.excs import SerializableBaseException, ExceptionWrapper
from twisted.web.http import Request

__author__ = 'mmalkov'


class RestJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime.datetime, datetime.date)):
            return o.isoformat()
        if hasattr(o, '__json__'):
            return o.__json__()
        if hasattr(o, '__unicode__'):
            return o.__unicode__()
        if hasattr(o, '__dict__'):
            return o.__dict__
        return o


def as_json(o):
    return json.dumps(o, ensure_ascii=False, cls=RestJsonEncoder, encoding='utf-8').encode('utf-8')


def api_method(func):
    @functools.wraps(func)
    @defer.inlineCallbacks
    def wrapper(*args, **kwargs):
        try:
            result = yield func(*args, **kwargs)
        except SerializableBaseException as e:
            result = e
        except Exception as e:
            result = ExceptionWrapper(e)
        if len(args) > 1 and isinstance(args[1], Request):
            args[1].setHeader('content-type', 'application/json; charset=utf-8')
        defer.returnValue(as_json(result))
    return wrapper


def safe_traverse(obj, *args, **kwargs):
    """Безопасное копание вглубь dict'а
    @param obj: точка входя для копания
    @param *args: ключи, по которым надо проходить
    @param default=None: возвращаемое значение, если раскопки не удались
    @rtype: any
    """
    default = kwargs.get('default', None)
    if obj is None:
        return default
    if len(args) == 0:
        raise ValueError(u'len(args) must be > 0')
    elif len(args) == 1:
        return obj.get(args[0], default)
    else:
        return safe_traverse(obj.get(args[0]), *args[1:], **kwargs)


def must_be_deferred(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return defer.maybeDeferred(func, *args, **kwargs)
    return wrapper


def safe_int(value):
    try:
        return int(value)
    except ValueError:
        return value


def get_args(request):
    content = request.content
    if content is not None:
        try:
            return json.loads(content.getvalue())
        except ValueError:
            pass
    # This is primarily for testing purposes - to pass arguments in url
    return dict(
        (key, value[0])
        for key, value in request.args.iteritems()
    )


def transfer_fields(dest, src, fields):
    for name in fields:
        setattr(dest, name, getattr(src, name))


class ThreadWrapper(object):
    def __init__(self, name=None):
        self.q = Queue()
        self.thread = None
        self.name = name

    def _cb(self, deferred, result):
        """
        Callback to be run on deferred function success
        This function is run in Thread

        :type deferred: twisted.internet.defer.Deferred
        :param deferred: Deferred with callback
        :param result: result to pass through
        :return:
        """
        from twisted.internet import reactor

        self.q.task_done()
        reactor.callFromThread(deferred.callback, result)
        return result

    def _eb(self, deferred, failure):
        """
        Errback to be run on deferred function fail
        This function is run in Thread

        :type deferred: twisted.internet.defer.Deferred
        :param deferred: Deferred with errback
        :param failure: failure to pass through
        :return:
        """
        from twisted.internet import reactor

        self.q.task_done()
        reactor.callFromThread(deferred.errback, failure)
        return failure

    def _run(self):
        """
        Wrapper's main loop, target of the Thread.
        This function is run in Thread

        :return:
        """
        while 1:
            func, args, kwargs, deferred = self.q.get(timeout=1)
            if not func:
                self.thread = None
                break

            defer.maybeDeferred(func, *args, **kwargs)\
                .addCallbacks(self._cb, self._eb, callbackArgs=(deferred,), errbackArgs=(deferred,))

    def call(self, func, *args, **kwargs):
        """
        Call function in Thread's call queue
        :param func: callable
        :return: Deferred which fires when function execution is done
        """
        deferred = defer.Deferred()
        self.q.put((func, args, kwargs, deferred))
        return deferred

    def start(self):
        """
        Start ThreadWrapper
        :return:
        """
        from threading import Thread
        self.thread = Thread(target=self._run, name=self.name)

    def stop(self):
        """
        Stop ThreadWrapper
        :return:
        """
        self.q.put((None, None, None, None))

    def synchronize(self, func):
        """
        Decorate function to be called inside this ThreadWrapper
        :param func: function
        :return: decorated function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
