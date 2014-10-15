#!/usr/bin/env python
# -*- coding: utf-8 -*-

from klein import Klein
from twisted.python.components import registerAdapter
from twisted.web.resource import IResource
from zope.interface import Interface, implementer

from coldstar.interfaces import ITmpLockService
from coldstar.utils import as_json


__author__ = 'viruzzz-kun'
__created__ = '05.10.2014'


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
        token = request.args.get('token', None)
        if token is None:
            return 'bla'
        result = self.service.prolong_tmp_lock(object_id, token.decode('hex'))
        return as_json(result)

    @app.route('/release_lock/<object_id>')
    def release_lock(self, request, object_id):
        try:
            token = request.args.get('token', None).decode('hex')
        except TypeError:
            return as_json(None)
        except ValueError:
            return as_json(None)
        result = self.service.release_lock(object_id, token)
        return as_json(result)


registerAdapter(RestService, ITmpLockService, IRestService)
registerAdapter(lambda service: service.app.resource(), IRestService, IResource)