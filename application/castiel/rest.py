# -*- coding: utf-8 -*-
from twisted.python.components import registerAdapter
from twisted.web.error import UnsupportedMethod
from twisted.web.resource import IResource, Resource
from twisted.web.util import Redirect
from zope.interface import implementer
from application.castiel.interfaces import ICasService
from lib.utils import api_method

__author__ = 'mmalkov'

@implementer(IResource)
class CastielWebResource(Resource):
    isLeaf = True
    cookie_name = 'CastielAuthToken'

    def __init__(self, castiel_service):
        Resource.__init__(self)
        self.service = castiel_service

    def render_GET(self, request):
        ppl = len(request.postpath)
        if ppl == 0 or ppl == 1 and not request.postpath[0]:
            return 'This is Castiel, angel of God'
        if ppl == 1:
            token = request.getCookie(self.cookie_name)
            if token:
                token = token.decode('hex')

            if request.postpath[0] == 'acquire':
                return self.acquire_token(request)

            elif request.postpath[0] == 'login':
                if request.method == 'GET':
                    return self.login_form()

                elif request.method == 'POST':
                    back = request.args.get('back', None)
                    result = self.acquire_token(request)
                    if back:
                        return Redirect(back[0])
                    return result

            elif request.postpath[0] == 'release':
                return self.release_token(token.decode('hex'))

            elif request.postpath[0] == 'check':
                return self.check_token(token.decode('hex'))

        request.setResponseCode(404)
        return '404 Not Found'

    @api_method
    def acquire_token(self, request):
        """
        Acquire auth token for login / password pair
        :param login:
        :param password:
        :return:
        """
        login = request.args['login'][0]
        password = request.args['password'][0]
        token = self.service.acquire_token(login, password)
        request.addCookie(self.cookie_name, token.encode('hex'), )

        return token.encode('hex')

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
        # Implicitly prolong token...
        self.prolong_token(token)
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