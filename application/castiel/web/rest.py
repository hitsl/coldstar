# -*- coding: utf-8 -*-

from twisted.internet import defer
from twisted.web.resource import IResource, Resource
from twisted.web.util import redirectTo
from zope.interface import implementer

from .root import CastielResourceMixin
from ..service import ERottenToken
from lib.excs import SerializableBaseException, ExceptionWrapper
from lib.utils import api_method, as_json


__author__ = 'mmalkov'


@implementer(IResource)
class CastielApiResource(Resource, CastielResourceMixin):
    isLeaf = True

    def __init__(self, castiel_service):
        Resource.__init__(self)
        self.service = castiel_service

    @defer.inlineCallbacks  # This is custom Twisted feature. See file 'twisted.patch.diff' for details
    def render(self, request):
        ppl = len(request.postpath)
        if ppl == 0 or ppl == 1 and not request.postpath[0]:
            defer.returnValue('I am Castiel, angel of God')

        if ppl == 1:
            if request.postpath[0] == 'acquire':
                result = yield self.acquire_token(request)
                defer.returnValue(result)

            elif request.postpath[0] == 'release':
                defer.returnValue(self.release_token(request))

            elif request.postpath[0] == 'check':
                defer.returnValue(self.check_token(request))

        request.setResponseCode(404)
        defer.returnValue('404 Not Found')

    @api_method
    @defer.inlineCallbacks
    def acquire_token(self, request):
        """
        Acquire auth token for login / password pair
        :param request:
        :return:
        """
        login = request.args['login'][0].decode('utf-8')
        password = request.args['password'][0].decode('utf-8')
        token = yield self.service.acquire_token(login, password)
        defer.returnValue({
            'token': token.encode('hex'),
        })

    @api_method
    def release_token(self, request):
        """
        Release previously acquired token
        :param request:
        :return:
        """
        try:
            return self.service.release_token(self._get_hex_token(request))
        except ERottenToken as e:
            print 'Rotten token', e.token.encode(hex)
            raise

    @api_method
    def check_token(self, request):
        """
        Check whether auth token is valid
        :param request:
        :return:
        """
        # Implicitly prolong token...
        return self.service.check_token(self._get_hex_token(request), True)

    @api_method
    def prolong_token(self, request):
        """
        Make token live longer
        :param request:
        :return:
        """
        try:
            return self.service.prolong_token(self._get_hex_token(request))
        except ERottenToken:
            raise
