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

    @app.route('/acquire_tmp_lock/<object_id>')
    def acquire_tmp_lock(self, request, object_id):
        try:
            result = self.service.acquire_tmp_lock(object_id, None)
        except SerializableBaseException, e:
            return as_json(e)
        except Exception, e:
            return as_json(ExceptionWrapper(e))
        else:
            return as_json(result)

    @app.route('/prolong_tmp_lock/<object_id>')
    def prolong_tmp_lock(self, request, object_id):
        try:
            token = request.args.get('token', None).decode('hex')
        except Exception, e:
            return as_json(ExceptionWrapper(e))
        try:
            result = self.service.prolong_tmp_lock(object_id, token)
        except SerializableBaseException, e:
            return as_json(e)
        except Exception, e:
            return as_json(ExceptionWrapper(e))
        else:
            return as_json(result)

    @app.route('/release_lock/<object_id>')
    def release_lock(self, request, object_id):
        try:
            token = request.args.get('token', None).decode('hex')
        except Exception, e:
            return as_json(ExceptionWrapper(e))
        try:
            result = self.service.release_lock(object_id, token)
        except SerializableBaseException, e:
            return as_json(e)
        except Exception, e:
            return as_json(ExceptionWrapper(e))
        else:
            return as_json(result)


registerAdapter(RestService, ITmpLockService, IRestService)
registerAdapter(lambda service: service.app.resource(), IRestService, IResource)