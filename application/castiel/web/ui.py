# -*- coding: utf-8 -*-
import os

import jinja2
from twisted.internet import defer
from twisted.web.resource import IResource, Resource
from twisted.web.static import File
from twisted.web.util import redirectTo
from zope.interface import implementer

from .root import CastielResourceMixin
from .session import ICastielWebSession
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
        fm = ICastielWebSession(session)

        return dict(
            get_flashed_messages=fm.get_flashed_messages,
            url_for=url_for,
            request=request,
        )

    def render_template(self, name, request, **kwargs):
        template = self.jinja_env.get_template(name)
        context = self.get_jinja_context(request)
        context.update(kwargs)
        return template.render(context).encode('utf-8')


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
        session = request.getSession()
        fm = ICastielWebSession(session)
        back = request.args.get('back', [request.getHeader('Referer') or '/'])[0]
        if not fm.back:
            fm.back = back
        if not self.service.check_token(token):
            # Token is invalid - proceed to login form
            return self.parent.render_template('login.html', request)
        else:
            # Token is valid - just redirect
            fm.back = None
            return redirectTo(back, request)

    @defer.inlineCallbacks
    def render_POST(self, request):
        session = request.getSession()
        fm = ICastielWebSession(session)
        back = fm.back
        try:
            login = request.args['login'][0].decode('utf-8')
            password = request.args['password'][0].decode('utf-8')
            token = yield self.service.acquire_token(login, password)
        except EInvalidCredentials:
            print 'Invalid credentials'
            fm.flash_message(dict(
                text=u"Неверное имя пользователя или пароль",
                severity='danger'
            ))
            defer.returnValue(redirectTo(request.uri, request))
        except ETokenAlreadyAcquired:
            fm.back = None
            defer.returnValue(redirectTo(back, request))
        else:
            token_txt = token.encode('hex')
            request.addCookie(self.cookie_name, token_txt)
            fm.back = None
            defer.returnValue(redirectTo(back, request))
