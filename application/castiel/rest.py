# -*- coding: utf-8 -*-
from twisted.python.components import registerAdapter
from twisted.web.resource import IResource, Resource
from zope.interface import implementer
from application.castiel.interfaces import ICasService
from lib.utils import api_method

__author__ = 'mmalkov'


@implementer(IResource)
class CastielWebResource(Resource):
    def __init__(self, castiel_service):
        Resource.__init__(self)
        self.service = castiel_service

    def render_GET(self, request):
        ppl = len(request.postpath)
        if ppl == 0 or ppl == 1 and not request.postpath[0]:
            return 'This is Castiel, angel of God'
        if ppl == 1:
            if request.postpath[0] == 'acquire':
                login = request.args['login'][0]
                password = request.args['password'][0]
                return self.acquire_token(login, password)
            elif request.postpath[0] == 'login':
                return self.login_form()
        elif ppl == 2:
            if request.postpath[0] == 'release':
                return self.release_token(request.postpath[1].decode('hex'))
            elif request.postpath[0] == 'check':
                return self.check_token(request.postpath[1].decode('hex'))
        request.setResponseCode(404)
        return '404 Not Found'

    @api_method
    def acquire_token(self, login, password):
        """
        Acquire auth token for login / password pair
        :param login:
        :param password:
        :return:
        """
        return self.service.acquire_token(login, password)

    @api_method
    def release_token(self, token):
        """
        Release previously acquired token
        :param token:
        :return:
        """
        return self.service.release_token(token)

    @api_method
    def check_token(self, token):
        """
        Check whether auth token is valid
        :param token:
        :return:
        """
        return self.service.check_token(token)

    @api_method
    def prolong_token(self, token):
        """
        Make token live longer
        :param token:
        :return:
        """
        return self.service.prolong_token(token)

    def login_form(self):
        return 'No form available at the moment'


registerAdapter(CastielWebResource, ICasService, IResource)