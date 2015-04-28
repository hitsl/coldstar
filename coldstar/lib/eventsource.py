# -*- coding: utf-8 -*-
from coldstar.lib.utils import as_json

__author__ = 'viruzzz-kun'


def make_event(data, event=None, id_=None, is_json=1):
    result = []
    if id_:
        result.append('id: %s' % id_)
    if event:
        result.append('event: %s' % event)
    if is_json:
        result.extend(map(lambda x: 'data: %s' % x, as_json(data).splitlines()))
    result.append('\n')
    return '\n'.join(result)