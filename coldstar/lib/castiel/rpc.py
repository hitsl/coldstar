# -*- coding: utf-8 -*-

from itsdangerous import json
from twisted.internet import defer
from twisted.web.resource import IResource, Resource
from zope.interface import implementer

from coldstar.lib.utils import api_method


__author__ = 'mmalkov'


@implementer(IResource)
class CastielApiResource(Resource):
    isLeaf = True

    def __init__(self, castiel_service):
        Resource.__init__(self)
        self.service = castiel_service

    @api_method
    # This is custom Twisted feature. See file 'twisted.patch.diff' for details
    def render(self, request):
        request.setHeader('Content-Type', 'application/json; charset=utf-8')
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
        j = self._get_args(request)
        login = j['login']
        password = j['password']
        token, deadline, user_id = yield self.service.acquire_token(login, password)
        defer.returnValue({
            'success': True,
            'token': token.encode('hex'),
            'deadline': deadline,
            'user_id': user_id,
        })

    @defer.inlineCallbacks
    def release_token(self, request):
        """
        Release previously acquired token
        :param request:
        :return:
        """
        j = self._get_args(request)
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
        j = self._get_args(request)
        # Don't implicitly prolong token
        user_id, deadline = yield self.service.check_token(j['token'].decode('hex'), False)
        defer.returnValue({
            'success': True,
            'user_id': user_id,
            'deadline': deadline,
            'token': j['token'],
        })

    @defer.inlineCallbacks
    def prolong_token(self, request):
        """
        Make token live longer
        :param request:
        :return:
        """
        j = self._get_args(request)
        success, deadline = yield self.service.prolong_token(j['token'].decode('hex'))
        defer.returnValue({
            'success': success,
            'deadline': deadline,
            'token': j['token'],
        })

    @defer.inlineCallbacks
    def is_valid_credentials(self, request):
        """
        Check whether credentials are valid
        :param request:
        :return:
        """
        j = self._get_args(request)
        user = yield self.service.is_valid_credentials(j['login'], j['password'])
        defer.returnValue({
            'success': True,
            'user_id': user.user_id,
        })

    @staticmethod
    def _get_args(request):
        content = request.content
        if content is not None:
            try:
                return json.loads(content.getvalue())
            except ValueError:
                pass
        # This is primarily for testing purposes - to pass arguments in url
        return dict(
            (key, value[0])
            for key, value in request.args.iteritems()
        )
