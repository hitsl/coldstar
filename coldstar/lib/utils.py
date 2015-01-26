# -*- coding: utf-8 -*-
import datetime
import json
import functools

from twisted.internet import defer

from coldstar.lib.excs import SerializableBaseException, ExceptionWrapper


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