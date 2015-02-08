#!/usr/bin/env python
# -*- coding: utf-8 -*-
import jinja2
from twisted.python.components import proxyForInterface, registerAdapter
from twisted.web.server import IRequest, Request, Session
from twisted.web.resource import Resource, IResource, getResourceFor
from twisted.web.static import File, Data
from zope.interface import implementer

from .interfaces import IWebSession

__author__ = 'viruzzz-kun'
__created__ = '08.02.2015'


class TemplatedResource(Resource):
    isLeaf = True

    def __init__(self, static_path, template_path, *args, **kwargs):
        Resource.__init__(self, *args, **kwargs)
        self.jinja_env = jinja2.Environment(
            extensions=['jinja2.ext.with_'],
            loader=jinja2.FileSystemLoader(template_path),
        )
        self.putChild('static', File(static_path))

    def render(self, request):

        def render_template(name, **kwargs):

            def url_for(endpoint, filename='', **kwargs):
                if endpoint == 'static':
                    if not filename:
                        raise RuntimeError('filename')
                    result = '/static/%s' % filename
                    if kwargs:
                        result = '?' + '&'.join('%s=%s' % item for item in kwargs.iteritems())
                    return result
                return ''

            session = request.getSession()
            fm = IWebSession(session)

            context = {
                'get_flashed_messages': fm.get_flashed_messages,
                'url_for': url_for,
                'request': request,
            }
            context.update(kwargs)

            template = self.jinja_env.get_template(name)
            return template.render(context).encode('utf-8')

        request.master_resource = self
        request.render_template = render_template
        resource = getResourceFor(self, request)
        resource.render(request)


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


registerAdapter(WebSession, Session, IWebSession)