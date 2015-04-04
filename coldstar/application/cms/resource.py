#!/usr/bin/env python
# -*- coding: utf-8 -*-
from twisted.internet import defer
from twisted.web.resource import Resource

__author__ = 'viruzzz-kun'
__created__ = '03.04.2015'


def post_request(url, data):
    from twisted.web.client import URI, HTTPClientFactory, nativeString
    from twisted.internet import ssl, reactor

    uri = URI.fromBytes(url)
    factory = HTTPClientFactory(url, 'POST', data, {'local-cms-request': '1'})
    reactor.connectSSL(nativeString(uri.host), uri.port, factory, ssl.ClientContextFactory())
    return factory


class CmsResource(Resource):
    isLeaf = 1

    def __init__(self, service):
        """
        :type service: coldstar.application.cms.service.CmsService
        :param service:
        :return:
        """
        Resource.__init__(self)
        self.service = service

    @defer.inlineCallbacks
    def render(self, request):
        """
        :type request: coldstar.lib.web.wrappers.TemplatedRequest
        :param request: 
        :return:
        """
        p = filter(None, request.postpath)
        if request.method == 'POST':
            if len(p) == 1 and p[0] == 'preview':
                result = yield post_request('https://moonworks/md/try', request.content).deferred
                defer.returnValue(result)
            elif len(p) > 1 and p[0] != 'preview':
                if p[0] == 'img':
                    self.service.post_img('/'.join(p[1:]), request.content)
                else:
                    self.service.post(p[0], '/'.join(p[1:]), request.content)
                defer.returnValue('OK')

        elif request.method == 'GET':
            if len(p) > 1:
                if p[0] == 'img':
                    request.setHeader('content-type', 'application/octet-stream')
                    defer.returnValue(self.service.get_img('/'.join(p[1:]), request))
                else:
                    request.setHeader('content-type', 'text/markdown; charset=utf-8')
                    defer.returnValue(self.service.get(p[0], '/'.join(p[1:]), request))

        request.setResponseCode(404)
        defer.returnValue('Endpoint not found')