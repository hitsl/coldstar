# -*- coding: utf-8 -*-
import os
import jinja2

from twisted.python.components import registerAdapter
from twisted.web.resource import IResource, Resource, getChildForRequest
from twisted.web.util import Redirect
from twisted.web.static import File
from zope.interface import implementer

from application.castiel.interfaces import ICasService
from application.castiel.service import ERottenToken
from lib.excs import SerializableBaseException
from lib.utils import api_method, as_json


__author__ = 'mmalkov'


class ENoToken(SerializableBaseException):
    def __init__(self):
        self.message = 'Token cookie is not set'


@implementer(IResource)
class CastielWebResource(Resource):
    isLeaf = True
    cookie_name = 'CastielAuthToken'

    def __init__(self, castiel_service):
        Resource.__init__(self)
        current_dir = os.path.abspath(os.path.dirname(__file__))
        self.jinja_env = jinja2.Environment(
            extensions=['jinja2.ext.with_'],
            loader=jinja2.FileSystemLoader(os.path.join(current_dir, 'templates')),
        )
        self.static_resource = File(os.path.join(current_dir, 'static'))
        # self.putChild('static', self.static_resource)
        self.service = castiel_service

    def render_GET(self, request):
        ppl = len(request.postpath)
        if ppl == 0 or ppl == 1 and not request.postpath[0]:
            return 'I am Castiel, angel of God'

        if ppl >= 1 and request.postpath[0] == 'static':
                request.prepath.append(request.postpath.pop(0))
                return getChildForRequest(self.static_resource, request).render(request)

        elif ppl == 1:
            if request.postpath[0] == 'acquire':
                return self.acquire_token(request)

            elif request.postpath[0] == 'login':
                if request.method == 'GET':
                    return self.login_form(request)

                elif request.method == 'POST':
                    return self.acquire_token(request)

            elif request.postpath[0] == 'release':
                return self.release_token(request)

            elif request.postpath[0] == 'check':
                return self.check_token(request)

        request.setResponseCode(404)
        return '404 Not Found'

    def acquire_token(self, request):
        """
        Acquire auth token for login / password pair
        :param request:
        :return:
        """
        back = request.args.get('back', None)
        login = request.args['login'][0]
        password = request.args['password'][0]
        token = self.service.acquire_token(login, password)
        token_txt = token.encode('hex')
        request.addCookie(self.cookie_name, token_txt)
        if back:
            return Redirect(back[0])
        return as_json(token_txt)

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
            # request.addCookie(self.cookie_name, '')
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
            request.addCookie(self.cookie_name, '')
            raise

    def login_form(self, request):
        def _uf(name, filename='', **kwargs):
            if name in ('static', '.static'):
                result = '/%s/%s' % ('/'.join(request.prepath), name)
                if filename:
                    result += '/%s' % filename
                if kwargs:
                    result += '?' + '&'.join('%s=%s' % item for item in kwargs.iteritems())
                return result
            return 'deded'
        def _gfm():
            return []
        template = self.jinja_env.get_template('login.html')
        return template.render(url_for=_uf, get_flashed_messages=_gfm).encode('utf-8')

    def _get_hex_token(self, request):
        token = request.getCookie(self.cookie_name)
        if token:
            print(token)
            return token.decode('hex')
        raise ENoToken()

registerAdapter(CastielWebResource, ICasService, IResource)