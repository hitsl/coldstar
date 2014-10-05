#!/usr/bin/env python
# -*- coding: utf-8 -*-
from klein import Klein
import json
from twisted.internet import defer
from twisted.python.components import registerAdapter
from zope.interface import Interface, implementer
from coldstar.interfaces import IColdStarService

__author__ = 'viruzzz-kun'
__created__ = '05.10.2014'


class RestJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, '__json__'):
            return o.__json__()
        if hasattr(o, '__unicode__'):
            return o.__unicode__()
        if hasattr(o, '__dict__'):
            return o.__dict__
        return o


def as_json(o):
    return json.dumps(o, ensure_ascii=False, cls=RestJsonEncoder, encoding='utf-8')


class IRestService(Interface):
    def acquire_tmp_lock(self, object_id, locker):
        pass

    def prolong_tmp_lock(self, object_id, token):
        pass

    def release_lock(self, object_id, token):
        pass


@implementer(IRestService)
class RestService(object):
    app = Klein()

    def __init__(self, service):
        """
        :type service: ColdStarService
        :param service:
        :return:
        """
        self.service = service

    @app.route('/')
    def index(self, request):
        return 'wtf'

    @app.route('/acquire_tmp_lock/<object_id>')
    def acquire_tmp_lock(self, request, object_id):
        result = self.service.acquire_tmp_lock(object_id, None)
        return as_json(result)

    @app.route('/prolong_tmp_lock/<object_id>')
    def prolong_tmp_lock(self, request, object_id):
        token = request.args.get('token', [None])
        if token is None:
            return 'bla'
        result = self.service.prolong_tmp_lock(object_id, token.decode('hex'))
        return as_json(result)

    @app.route('/release_lock/<object_id>')
    def release_lock(self, request, object_id):
        token = request.args.get('token', [None])
        if token is None:
            return 'blah'
        result = self.service.release_lock(object_id, token.decode('hex'))
        return as_json(result)

    @app.route('/test')
    @defer.inlineCallbacks
    def test(self, request):
        from twisted.internet import reactor
        d = defer.Deferred()
        reactor.callLater(3, lambda: d.callback('Nyan'))
        result = yield d
        print(result)
        defer.returnValue(result)


registerAdapter(RestService, IColdStarService, IRestService)
