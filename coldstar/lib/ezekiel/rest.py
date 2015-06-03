#!/usr/bin/env python
# -*- coding: utf-8 -*-
import blinker
from coldstar.lib.excs import Unauthorized, UnknownCommand

from twisted.web.resource import IResource, Resource
from zope.interface import implementer

from coldstar.lib.utils import api_method
from .interfaces import IRestService

__author__ = 'viruzzz-kun'
__created__ = '05.10.2014'


boot = blinker.signal('coldstar:boot')
boot_ezekiel = blinker.signal('coldstar.lib.ezekiel:boot')
boot_web = blinker.signal('coldstar.lib.web:boot')
boot_rest = blinker.signal('coldstar.lib.ezekiel.rest:boot')
boot_cas = blinker.signal('coldstar.lib.castiel:boot')


@implementer(IResource, IRestService)
class EzekielRestResource(Resource):
    isLeaf = True

    def __init__(self, config):
        Resource.__init__(self)
        self.service = None
        self.cas = None
        self.web_service = None
        self.cors_domain = '*'
        boot.connect(self.boot)
        boot_ezekiel.connect(self.boot_ezekiel)
        boot_web.connect(self.boot_web)
        boot_cas.connect(self.boot_cas)

    @api_method
    def render(self, request):
        """
        :type request: coldstar.lib.web.wrappers.TemplatedRequest
        :param request:
        :return:
        """
        request.setHeader('Access-Control-Allow-Origin', self.cors_domain)
        if request.method == 'OPTIONS' and request.requestHeaders.hasHeader('Access-Control-Request-Method'):
            # Preflight Request
            request.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            request.setHeader('Access-Control-Allow-Headers', 'Content-Type')
            request.setHeader('Access-Control-Max-Age', '600')
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

    def boot(self, root):
        print 'Ezekiel.Rest: boot...'
        boot_rest.send(self)

    def boot_ezekiel(self, ezekiel):
        self.service = ezekiel
        print 'Ezekiel.Rest: Service connected'

    def boot_web(self, web):
        self.web_service = web
        web.root_resource.putChild('ezekiel', self)

    def boot_cas(self, cas):
        self.cas = cas
        print 'Ezekiel.Rest: Cas connected'


def make(config):
    return EzekielRestResource(config)