#!/usr/bin/env python
# -*- coding: utf-8 -*-
from urllib import urlencode

import jinja2
from twisted.python.components import registerAdapter, Componentized
from twisted.spread.flavors import Copyable
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

        template = self.site.jinja_env.get_template(name)
        return template.render(context).encode('utf-8')

    def rememberAppPath(self):
        self.currentAppPath = '/'.join(self.prepath)

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
            result = '/%s/%s' % (self.currentAppPath, filename)
        if kwargs:
            result = '%s?%s' % (result, urlencode(kwargs.iteritems()))
        return result


@implementer(IWebSession)
class WebSession(object):
    def __init__(self, session):
        self.flashed_messages = []
        self.back = None

    def get_flashed_messages(self):
        messages, self.flashed_messages = self.flashed_messages, []
        return messages

    def flash_message(self, message):
        self.flashed_messages.append(message)


@implementer(ITemplatedSite)
class TemplatedSite(Site):
    requestFactory = TemplatedRequest

    def __init__(self, root_resource, static_path, template_path, *args, **kwargs):
        Site.__init__(self, root_resource, *args, **kwargs)
        jinja_loader = self.__jinja_loader = jinja2.FileSystemLoader(template_path)
        self.jinja_env = jinja2.Environment(
            extensions=['jinja2.ext.with_'],
            loader=jinja_loader,
        )
        root_resource.putChild('static', File(static_path))

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