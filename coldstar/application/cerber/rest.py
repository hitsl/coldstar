#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twisted.python.components import registerAdapter
from twisted.web.resource import IResource, Resource
from zope.interface import implementer

from coldstar.lib.utils import api_method
from .interfaces import IRestService
from .service import ITmpLockService


__author__ = 'viruzzz-kun'
__created__ = '05.10.2014'


@implementer(IResource, IRestService)
class ColdStarRestResource(Resource):
    isLeaf = True

    def __init__(self, coldstar_service):
        Resource.__init__(self)
        self.service = coldstar_service

    @api_method
    def render_GET(self, request):
        """
        :type request: coldstar.lib.web.wrappers.Request
        :param request:
        :return:
        """
        request.setHeader('content-type', 'application/json; charset=utf-8')
        if len(request.postpath) == 2:
            command, object_id = request.postpath
            token = request.args.get('token', [''])[0]
            locker = request.args.get('locker', [None])[0]
            if command == 'acquire':
                return self.acquire_tmp_lock(object_id, locker)
            elif command == 'prolong':
                return self.prolong_tmp_lock(object_id, token.decode('hex'))
            elif command == 'release':
                return self.release_lock(object_id, token.decode('hex'))
        request.setResponseCode(404)
        return '404 Not Found'

    @api_method
    def acquire_tmp_lock(self, object_id, locker):
        return self.service.acquire_tmp_lock(object_id, locker)

    @api_method
    def prolong_tmp_lock(self, object_id, token):
        return self.service.prolong_tmp_lock(object_id, token)

    @api_method
    def release_lock(self, object_id, token):
        return self.service.release_lock(object_id, token)


registerAdapter(ColdStarRestResource, ITmpLockService, IResource)