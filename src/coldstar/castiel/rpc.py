# -*- coding: utf-8 -*-

import time
from libcoldstar.plugin_helpers import ColdstarPlugin, Dependency

from twisted.internet import defer
from twisted.web.resource import IResource, Resource
from zope.interface import implementer
from libcoldstar.utils import api_method, get_args


__author__ = 'mmalkov'


@implementer(IResource)
class CastielApiResource(Resource, ColdstarPlugin):
    isLeaf = True

    service = Dependency('coldstar.castiel')
    web = Dependency('libcoldstar.web')
    cors_domain = '*'

    @api_method
    # This is custom Twisted feature. See file 'twisted.patch.diff' for details
    def render(self, request):
        """
        :type request: libcoldstar.web.wrappers.TemplatedRequest
        :param request:
        :return:
        """
        if self.web.crossdomain(request):
            return ''

        request.postpath = filter(None, request.postpath)
        ppl = len(request.postpath)
        if ppl == 0:
            return 'I am Castiel, angel of God'

        elif ppl == 1:
            leaf = request.postpath[0]
            if leaf == 'acquire':
                return self.acquire_token(request)

            elif leaf == 'release':
                return self.release_token(request)

            elif leaf == 'check':
                return self.check_token(request)

            elif leaf == 'prolong':
                return self.prolong_token(request)

            elif leaf == 'valid':
                return self.is_valid_credentials(request)

        request.setResponseCode(404)
        return '404 Not Found'

    @defer.inlineCallbacks
    def acquire_token(self, request):
        """
        Acquire auth token for login / password pair
        :param request:
        :return:
        """
        j = get_args(request)
        login = j['login']
        password = j['password']
        ato = yield self.service.acquire_token(login, password)
        defer.returnValue({
            'success': True,
            'token': ato.token.encode('hex'),
            'deadline': ato.deadline,
            'ttl': ato.deadline - time.time(),
            'user_id': ato.user_id,
        })

    @defer.inlineCallbacks
    def release_token(self, request):
        """
        Release previously acquired token
        :param request:
        :return:
        """
        j = get_args(request)
        result = yield self.service.release_token(j['token'].decode('hex'))
        defer.returnValue({
            'success': result,
            'token': j['token'],
        })

    @defer.inlineCallbacks
    def check_token(self, request):
        """
        Check whether auth token is valid
        :param request:
        :return:
        """
        j = get_args(request)
        prolong = j.get('prolong', False)
        hex_token = j.get('token', '')
        if len(hex_token) != 32:
            raise Exception(u'Плохой токен аутентификации')
        user_id, deadline = yield self.service.check_token(hex_token.decode('hex'), prolong)
        defer.returnValue({
            'success': True,
            'user_id': user_id,
            'deadline': deadline,
            'ttl': deadline - time.time(),
            'token': hex_token,
        })

    @defer.inlineCallbacks
    def prolong_token(self, request):
        """
        Make token live longer
        :param request:
        :return:
        """
        j = get_args(request)
        success, deadline = yield self.service.prolong_token(j['token'].decode('hex'))
        defer.returnValue({
            'success': success,
            'deadline': deadline,
            'ttl': deadline - time.time(),
            'token': j['token'],
        })

    @defer.inlineCallbacks
    def is_valid_credentials(self, request):
        """
        Check whether credentials are valid
        :param request:
        :return:
        """
        j = get_args(request)
        user = yield self.service.is_valid_credentials(j['login'], j['password'])
        defer.returnValue({
            'success': True,
            'user_id': user.user_id,
        })