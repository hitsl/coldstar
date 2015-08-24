#!/usr/bin/env python
# -*- coding: utf-8 -*-
from urllib import urlencode

import jinja2
from jinja2.exceptions import TemplateNotFound
from zope.interface import implementer

from twisted.internet import defer
from twisted.python import components, reflect, log
from twisted.python.components import registerAdapter, Componentized
from twisted.python.compat import intToBytes

from twisted.web import resource, html, http, error, microdom
from twisted.web.server import Request, Session, Site, NOT_DONE_YET, supportedMethods
from twisted.web.static import File

from ..plugin_helpers import ColdstarPlugin, Dependency
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
        :rtype: libcoldstar.castiel.service.AuthTokenObject | None
        :return:
        """
        cas = getattr(self.site, 'cas', None)
        if cas is not None:
            # FIXME: Cookie name should be configurable
            token_hex = self.getCookie('authToken')
            if not token_hex:
                return
            token = token_hex.decode('hex')
            return cas.get_user_quick(token)

    @property
    def user_agent(self):
        if not hasattr(self, '__user_agent'):
            from libcoldstar.web.useragents import UserAgent
            self.__user_agent = UserAgent(self.getHeader('User-Agent'))
        return self.__user_agent

    def get_content_type(self):
        content_type = self.requestHeaders.getRawHeaders('content-type', [])
        if content_type:
            return content_type[0].split(';', 1)[0].split('/')
        return None, None

    def getClientIP(self):
        if self.requestHeaders.hasHeader('x-forwarded-for'):
            return self.requestHeaders.getRawHeaders(b"x-forwarded-for")[0].split(b",")[0].strip()
        if self.requestHeaders.hasHeader('x-real-ip'):
            return self.requestHeaders.getRawHeaders(b"x-real-ip")[0].split(b",")[0].strip()
        return Request.getClientIP(self)

    # This allows us to use Deferred as return value from Resource.render(request)
    @defer.inlineCallbacks
    def render(self, resrc):
        """
        Ask a resource to render itself.

        @param resrc: a L{twisted.web.resource.IResource}.
        """
        try:
            body = yield defer.maybeDeferred(resrc.render, self)
        except error.UnsupportedMethod as e:
            allowedMethods = e.allowedMethods
            if (self.method == b"HEAD") and (b"GET" in allowedMethods):
                # We must support HEAD (RFC 2616, 5.1.1).  If the
                # resource doesn't, fake it by giving the resource
                # a 'GET' request and then return only the headers,
                # not the body.
                log.msg("Using GET to fake a HEAD request for %s" %
                        (resrc,))
                self.method = b"GET"
                self._inFakeHead = True
                body = resrc.render(self)

                if body is NOT_DONE_YET:
                    log.msg("Tried to fake a HEAD request for %s, but "
                            "it got away from me." % resrc)
                    # Oh well, I guess we won't include the content length.
                else:
                    self.setHeader(b'content-length', intToBytes(len(body)))

                self._inFakeHead = False
                self.method = b"HEAD"
                self.write(b'')
                self.finish()
                return

            if self.method in (supportedMethods):
                # We MUST include an Allow header
                # (RFC 2616, 10.4.6 and 14.7)
                self.setHeader('Allow', ', '.join(allowedMethods))
                s = ('''Your browser approached me (at %(URI)s) with'''
                     ''' the method "%(method)s".  I only allow'''
                     ''' the method%(plural)s %(allowed)s here.''' % {
                         'URI': microdom.escape(self.uri),
                         'method': self.method,
                         'plural': ((len(allowedMethods) > 1) and 's') or '',
                         'allowed': ', '.join(allowedMethods)
                     })
                epage = resource.ErrorPage(http.NOT_ALLOWED,
                                           "Method Not Allowed", s)
                body = epage.render(self)
            else:
                epage = resource.ErrorPage(
                    http.NOT_IMPLEMENTED, "Huh?",
                    "I don't know how to treat a %s request." %
                    (microdom.escape(self.method.decode("charmap")),))
                body = epage.render(self)
        except Exception as e:
            body = resource.ErrorPage(
                http.INTERNAL_SERVER_ERROR,
                "Request failed",
                "Request: " + html.PRE(reflect.safe_repr(self)) + "<br />" +
                "Resource: " + html.PRE(reflect.safe_repr(resrc)) + "<br />" +
                "Value: " + html.PRE(reflect.safe_repr(e))).render(self)

        if body == NOT_DONE_YET:
            return
        if not isinstance(body, bytes):
            body = resource.ErrorPage(
                http.INTERNAL_SERVER_ERROR,
                "Request did not return bytes",
                "Request: " + html.PRE(reflect.safe_repr(self)) + "<br />" +
                "Resource: " + html.PRE(reflect.safe_repr(resrc)) + "<br />" +
                "Value: " + html.PRE(reflect.safe_repr(body))).render(self)

        if self.method == b"HEAD":
            if len(body) > 0:
                # This is a Bad Thing (RFC 2616, 9.4)
                log.msg("Warning: HEAD request %s for resource %s is"
                        " returning a message body."
                        "  I think I'll eat it."
                        % (self, resrc))
                self.setHeader(b'content-length',
                               intToBytes(len(body)))
            self.write(b'')
        else:
            self.setHeader(b'content-length',
                           intToBytes(len(body)))
            self.write(body)
        self.finish()


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


@implementer(ITemplatedSite)
class TemplatedSite(Site, ColdstarPlugin):
    requestFactory = TemplatedRequest

    cas = Dependency('coldstar.castiel')

    def __init__(self, root_resource, *args, **kwargs):
        """
        :param castiel_service:
        :param static_path:
        :param template_path:
        """

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

        Site.__init__(self, root_resource, *args, **kwargs)

    def add_loader_path(self, path):
        self.__jinja_loader.searchpath.append(path)


class DefaultRootResource(resource.Resource):
    def __init__(self):
        from twisted.web.static import Data
        resource.Resource.__init__(self)
        self.putChild('', Data(u"""
<!DOCTYPE html>
<html>
<head><style>body { color: #fff; background-color: #027eae; font-family: "Segoe UI", "Lucida Grande", "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 16px; }
a, a:visited, a:hover { color: #fff; }</style></head>
<body><h1>ColdStar</h1><h2>Подсистема всякой ерунды</h2>Давайте придумаем более человеческое название...</body>
</html>""".encode('utf-8'), 'text/html; charset=utf-8'))


class AutoRedirectResource(resource.Resource):
    def render(self, request):
        """ Redirect to the resource with a trailing slash if it was omitted
        :type request: TemplatedRequest
        :param request:
        :return:
        """
        request.redirect(request.uri + '/')
        return ""


registerAdapter(WebSession, Session, IWebSession)