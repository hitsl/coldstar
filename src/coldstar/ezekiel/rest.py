#!/usr/bin/env python
# -*- coding: utf-8 -*-

from libcoldstar.excs import Unauthorized, UnknownCommand
from libcoldstar.plugin_helpers import ColdstarPlugin, Dependency
from twisted.web.resource import IResource, Resource
from zope.interface import implementer
from libcoldstar.utils import api_method
from .interfaces import IRestService

__author__ = 'viruzzz-kun'
__created__ = '05.10.2014'


@implementer(IResource, IRestService)
class EzekielRestResource(Resource, ColdstarPlugin):
    signal_name = 'coldstar.ezekiel.rest'
    isLeaf = True

    service = Dependency('coldstar.ezekiel')
    cas = Dependency('coldstar.castiel')
    web = Dependency('libcoldstar.web')

    @api_method
    def render(self, request):
        """
        :type request: libcoldstar.web.wrappers.TemplatedRequest
        :param request:
        :return:
        """
        if self.web.crossdomain(request, True):
            return ''

        request.setHeader('Content-Type', 'application/json; charset=utf-8')
        pp = filter(None, request.postpath)
        if len(pp) == 2:
            command, object_id = pp
            if command == 'acquire':
                locker_object = request.get_auth()
                if not locker_object:
                    request.setResponseCode(403)
                    raise Unauthorized()
                locker_id = locker_object.user_id
                return self.acquire_tmp_lock(object_id, locker_id)
            elif command == 'prolong':
                token = request.args.get('token', [''])[0]
                return self.prolong_tmp_lock(object_id, token.decode('hex'))
            elif command == 'release':
                token = request.args.get('token', [''])[0]
                return self.release_lock(object_id, token.decode('hex'))
            raise UnknownCommand(command)
        request.setResponseCode(404)

    def acquire_tmp_lock(self, object_id, locker):
        return self.service.acquire_tmp_lock(object_id, locker)

    def prolong_tmp_lock(self, object_id, token):
        return self.service.prolong_tmp_lock(object_id, token)

    def release_lock(self, object_id, token):
        return self.service.release_lock(object_id, token)

    @web.on
    def boot_web(self, web):
        web.root_resource.putChild('ezekiel', self)


def make(config):
    return EzekielRestResource()
