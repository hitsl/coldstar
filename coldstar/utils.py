# -*- coding: utf-8 -*-
import datetime
import json

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