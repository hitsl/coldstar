#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twisted.python.components import registerAdapter
from twisted.web.resource import IResource
from zope.interface import implementer

from klein import Klein
from coldstar.excs import SerializableBaseException, ExceptionWrapper
from coldstar.interfaces import ITmpLockService, IRestService
from coldstar.utils import as_json


__author__ = 'viruzzz-kun'
__created__ = '05.10.2014'


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

    @app.handle_errors(SerializableBaseException)
    def handle_sbe_exception(self, request, failure):
        request.setResponseCode(200)
        return as_json(failure.value)

    @app.handle_errors(Exception)
    def handle_any_error(self, request, failure):
        request.setResponseCode(500)
        return as_json(ExceptionWrapper(failure.value))

    @app.route('/acquire/<object_id>')
    def acquire_tmp_lock(self, request, object_id):
        return as_json(self.service.acquire_tmp_lock(object_id, None))

    @app.route('/prolong/<object_id>')
    def prolong_tmp_lock(self, request, object_id):
        token = request.args.get('token', None).decode('hex')
        result = self.service.prolong_tmp_lock(object_id, token)
        return as_json(result)

    @app.route('/release/<object_id>')
    def release_lock(self, request, object_id):
        token = request.args.get('token', None).decode('hex')
        result = self.service.release_lock(object_id, token)
        return as_json(result)


registerAdapter(RestService, ITmpLockService, IRestService)
registerAdapter(lambda service: service.app.resource(), IRestService, IResource)