# -*- coding: utf-8 -*-
from coldstar.lib.utils import as_json

__author__ = 'viruzzz-kun'


def make_event(data, event=None, id_=None, is_json=1):
    result = []
    if id_:
        result.append(b'id: %s' % id_)
    if event:
        result.append(b'event: %s' % event)
    if is_json:
        result.extend(map(lambda x: b'data: %s' % x, as_json(data).splitlines()))
    result.append(b'\n')
    result = b'\n'.join(result)
    if isinstance(result, unicode):
        result = result.encode('utf-8')
    return result