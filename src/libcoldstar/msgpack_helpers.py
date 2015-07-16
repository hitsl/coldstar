#!/usr/bin/env python
# -*- coding: utf-8 -*-
import msgpack

__author__ = 'viruzzz-kun'
__created__ = '05.04.2015'


def __encode_hook(obj):
    if isinstance(obj, set):
        return msgpack.ExtType(0, dump(sorted(obj)))
    elif hasattr(obj, 'msgpack'):
        if hasattr(obj, '__getstate__'):
            state = obj.__getstate__()
        elif hasattr(obj, '__dict__'):
            state = obj.__dict__
        else:
            raise msgpack.PackValueError('Cannot pack object %r' % obj)
        klass = obj.__class__.__name__
        module = obj.__module__
        return msgpack.ExtType(1, dump([module, klass, state]))
    return obj


def __ext_hook(code, data):
    if code == 0:
        return set(load(data))
    elif code == 1:
        mod, klass, state = load(data)
        module = __import__(mod, globals(), locals(), [klass])
        obj = getattr(module, klass)()
        obj.__setstate__(state)
        return obj
    return msgpack.ExtType(code, data)


def load(chunk, **kwargs):
    return msgpack.unpackb(chunk, ext_hook=__ext_hook, encoding='utf-8', **kwargs)


def dump(o):
    return msgpack.packb(o, default=__encode_hook, use_bin_type=True)
