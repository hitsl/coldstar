# -*- coding: utf-8 -*-
import os

import jinja2
from twisted.internet import defer
from twisted.web.resource import IResource, Resource
from twisted.web.static import File
from twisted.web.util import redirectTo
from zope.interface import implementer

from .root import CastielResourceMixin
from .session import IFlashedMessages
from ..service import EInvalidCredentials, ETokenAlreadyAcquired


__author__ = 'viruzzz-kun'


@implementer(IResource)
class CastielUserResource(Resource, CastielResourceMixin):
    cookie_name = 'CastielAuthToken'

    def __init__(self, castiel_service):
        Resource.__init__(self)
        current_dir = os.path.abspath(os.path.dirname(__file__))
        self.jinja_env = jinja2.Environment(
            extensions=['jinja2.ext.with_'],
            loader=jinja2.FileSystemLoader(os.path.join(current_dir, 'templates')),
        )
        self.static_resource = File(os.path.join(current_dir, 'static'))

        self.login_resource = CastielLoginResource(castiel_service)
        self.login_resource.parent = self

        self.putChild('login', self.login_resource)
        self.putChild('static', self.static_resource)

    def get_jinja_context(self, request):
        def url_for(name, filename='', **kwargs):
            if name in ('static', '.static'):
                result = '/%s/%s' % ('/'.join(request.prepath[:-1]), name)
                if filename:
                    result += '/%s' % filename
                if kwargs:
                    result += '?' + '&'.join('%s=%s' % item for item in kwargs.iteritems())
                return result
            return 'deded'

        session = request.getSession()
        fm = IFlashedMessages(session)

        return dict(
            get_flashed_messages=fm.get_flashed_messages,
            url_for=url_for,
            request=request,
        )


@implementer(IResource)
class CastielLoginResource(Resource, CastielResourceMixin):
    isLeaf = True
    parent = None

    def __init__(self, castiel_service):
        Resource.__init__(self)
        self.service = castiel_service

    def render_GET(self, request):
        token = request.getCookie(self.cookie_name)
        if token:
            token = token.decode('hex')
        back = request.args.get('back', ['/'])[0]

        if not self.service.check_token(token):
            # Token is invalid - proceed to login form
            template = self.parent.jinja_env.get_template('login.html')
            context = self.parent.get_jinja_context(request)
            return template.render(
                **context
            ).encode('utf-8')
        else:
            # Token is valid - just redirect
            return redirectTo(back, request)

    @defer.inlineCallbacks
    def render_POST(self, request):
        back = request.args.get('back', ['/'])[0]
        try:
            login = request.args['login'][0].decode('utf-8')
            password = request.args['password'][0].decode('utf-8')
            token = yield self.service.acquire_token(login, password)
        except EInvalidCredentials:
            print 'Invalid credentials'
            session = request.getSession()
            fm = IFlashedMessages(session)
            fm.flash_message(dict(
                text=u"Неверное имя пользователя или пароль",
                severity='danger'
            ))
            defer.returnValue(redirectTo(request.uri, request))
        except ETokenAlreadyAcquired:
            defer.returnValue(redirectTo(back, request))
        else:
            token_txt = token.encode('hex')
            request.addCookie(self.cookie_name, token_txt)
            defer.returnValue(redirectTo(back, request))
