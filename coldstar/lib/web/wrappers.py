#!/usr/bin/env python
# -*- coding: utf-8 -*-
from urllib import urlencode

import blinker
import jinja2
from jinja2.exceptions import TemplateNotFound
from twisted.python import components
from twisted.python.components import registerAdapter, Componentized
from twisted.web.resource import Resource
from twisted.web.server import Request, Session, Site
from twisted.web.static import File

from zope.interface import implementer
from .interfaces import ITemplatedSite, IWebSession, ITemplatedRequest


__author__ = 'viruzzz-kun'
__created__ = '08.02.2015'

@implementer(ITemplatedRequest)
class TemplatedRequest(Request):
    currentAppPath = '/'

    def render_template(self, name, **kwargs):
        if not ITemplatedSite.providedBy(self.site):
            raise RuntimeError('Site does not provide templating capabilities')
        session = self.getSession()
        fm = IWebSession(session)

        context = {
            'get_flashed_messages': fm.get_flashed_messages,
            'url_for': self.__url_for,
            'request': self,
        }
        context.update(kwargs)

        try:
            template = self.site.jinja_env.get_template(name)
            return template.render(context).encode('utf-8')
        except TemplateNotFound as e:
            print('Template not found filename="%s", name="%s"' % (e.filename, e.name))

    def rememberAppPath(self):
        self.currentAppPath = '/' + '/'.join(self.prepath)

    def __url_for(self, endpoint, **kwargs):
        result = '/'
        if endpoint == 'static':
            filename = kwargs.pop('filename')
            if not filename:
                raise RuntimeError('filename')
            result = '/static/%s' % filename
        elif endpoint == '.static':
            filename = kwargs.pop('filename')
            if not filename:
                raise RuntimeError('filename')
            result = '%s/%s' % (self.currentAppPath, filename)
        if kwargs:
            result = '%s?%s' % (result, urlencode(kwargs.iteritems()))
        return result

    def get_auth(self):
        """
        :rtype: coldstar.lib.castiel.service.AuthTokenObject | None
        :return:
        """
        cas = getattr(self.site, 'cas', None)
        if cas is not None:
            # FIXME: Cookie name should be configurable
            token = self.getCookie('CastielAuthToken').decode('hex')
            return cas.get_user_quick(token)

    @property
    def user_agent(self):
        if not hasattr(self, '__user_agent'):
            from .useragents import UserAgent
            self.__user_agent = UserAgent(self.getHeader('User-Agent'))
        return self.__user_agent


@implementer(IWebSession)
class WebSession(components.Componentized):
    def __init__(self, session):
        Componentized.__init__(self)
        self.session = session
        self.flashed_messages = []
        self.back = None

    def get_flashed_messages(self):
        messages, self.flashed_messages = self.flashed_messages, []
        return messages

    def flash_message(self, message):
        self.flashed_messages.append(message)


cas_boot = blinker.signal('coldstar.lib.castiel:boot')


@implementer(ITemplatedSite)
class TemplatedSite(Site):
    requestFactory = TemplatedRequest

    def __init__(self, root_resource, *args, **kwargs):
        """
        :param castiel_service:
        :param static_path:
        :param template_path:
        """

        self.castiel = kwargs.pop('castiel_service', None)

        static_path = kwargs.pop('static_path', None)
        if static_path:
            root_resource.putChild('static', File(static_path))

        template_path = kwargs.pop('template_path', None)
        if template_path:
            self.__jinja_loader = jinja2.FileSystemLoader(template_path)
            self.jinja_env = jinja2.Environment(
                extensions=['jinja2.ext.with_'],
                loader=self.__jinja_loader,
            )

        self.cas = None
        Site.__init__(self, root_resource, *args, **kwargs)
        cas_boot.connect(self.cas_boot)

    def cas_boot(self, sender):
        self.cas = sender

    def add_loader_path(self, path):
        self.__jinja_loader.searchpath.append(path)


class DefaultRootResource(Resource):
    def __init__(self):
        from twisted.web.static import Data
        Resource.__init__(self)
        self.putChild('', Data(u"""
<!DOCTYPE html>
<html>
<head><style>body { color: #fff; background-color: #027eae; font-family: "Segoe UI", "Lucida Grande", "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 16px; }
a, a:visited, a:hover { color: #fff; }</style></head>
<body><h1>ColdStar</h1><h2>Подсистема всякой ерунды</h2>Давайте придумаем более человеческое название...</body>
</html>""".encode('utf-8'), 'text/html; charset=utf-8'))


class AutoRedirectResource(Resource):
    def render(self, request):
        """ Redirect to the resource with a trailing slash if it was omitted
        :type request: TemplatedRequest
        :param request:
        :return:
        """
        request.redirect(request.uri + '/')
        return ""


registerAdapter(WebSession, Session, IWebSession)