#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twisted.internet import defer
from twisted.web.resource import IResource, Resource
from twisted.web.util import redirectTo
from zope.interface import implementer

from .exceptions import EExpiredToken, ETokenAlreadyAcquired
from coldstar.lib.excs import SerializableBaseException
from coldstar.lib.web.interfaces import IWebSession
from coldstar.lib.castiel.exceptions import EInvalidCredentials


__author__ = 'viruzzz-kun'
__created__ = '08.02.2015'


@implementer(IResource)
class CastielLoginResource(Resource):
    isLeaf = True

    def __init__(self, castiel_service, web_service):
        Resource.__init__(self)
        self.service = castiel_service
        self.web_service = web_service

    @defer.inlineCallbacks
    def render_GET(self, request):
        """
        :type request: coldstar.lib.web.wrappers.TemplatedRequest
        :param request:
        :return:
        """
        token = request.getCookie(self.web_service.cookie_name)
        session = request.getSession()
        fm = IWebSession(session)
        if 'back' in request.args:
            fm.back = request.args['back'][0]
        elif not fm.back:
            fm.back = request.getHeader('Referer') or '/'
        try:
            if token:
                token = token.decode('hex')
                yield self.service.check_token(token)
            else:
                defer.returnValue(request.render_template('login.html'))
        except EExpiredToken:
            defer.returnValue(request.render_template('login.html'))
        else:
            # Token is valid - just redirect
            back, fm.back = fm.back, None
            defer.returnValue(redirectTo(back, request))

    @defer.inlineCallbacks
    def render_POST(self, request):
        """
        :type request: coldstar.lib.web.wrappers.TemplatedRequest
        :param request:
        :return:
        """
        session = request.getSession()
        fm = IWebSession(session)
        back = fm.back or request.args.get('back', ['/'])[0]
        try:
            login = request.args['login'][0].decode('utf-8')
            password = request.args['password'][0].decode('utf-8')
            ato = yield self.service.acquire_token(login, password)
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
            token_txt = ato.token.encode('hex')
            source_domain = request.getHeader('Host').split(':')[0]
            cookie_domain = self.web_service.get_cookie_domain(source_domain)
            request.addCookie(
                self.web_service.cookie_name, token_txt, domain=cookie_domain,
                path='/', comment='Castiel Auth Cookie'
            )
            fm.back = None
            defer.returnValue(redirectTo(back, request))


class ENoToken(SerializableBaseException):
    def __init__(self):
        self.message = 'Token cookie is not set'


