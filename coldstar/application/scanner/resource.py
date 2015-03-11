# -*- coding: utf-8 -*-
from twisted.internet import defer
from twisted.internet.defer import CancelledError
from twisted.python.components import registerAdapter
from twisted.web.resource import Resource, IResource
from twisted.web.server import NOT_DONE_YET
from coldstar.application.scanner.interfaces import IScanService
from coldstar.lib.utils import api_method

__author__ = 'viruzzz-kun'


class ScanResource(Resource):
    isLeaf = 1

    def __init__(self, service):
        Resource.__init__(self)
        self.service = service

    def render(self, request):
        """
        :type request: coldstar.lib.web.wrappers.TemplatedRequest
        :param request:
        :return:
        """
        request.setHeader('Access-Control-Allow-Origin', request.site.cors_domain)
        if request.method == 'OPTIONS' and request.requestHeaders.hasHeader('Access-Control-Request-Method'):
            # Preflight Request
            request.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            request.setHeader('Access-Control-Allow-Headers', 'Content-Type')
            request.setHeader('Access-Control-Max-Age', '600')
            return ''

        request.postpath = filter(None, request.postpath)
        ppl = len(request.postpath)
        if ppl == 0:
            return 'I am Scanner'

        elif ppl == 1:
            leaf = request.postpath[0]
            if leaf == 'list':
                request.setHeader('Content-Type', 'application/json; charset=utf-8')
                return self.scanners(request)
            elif leaf == 'scan':
                request.setHeader('Content-Type', 'image/png')
                return self.scan(request)
        request.setResponseCode(404)
        return ''

    @api_method
    @defer.inlineCallbacks
    def scanners(self, request):
        force = bool(request.args.get('force', [0])[0])
        result = yield self.service.getScanners(force)
        defer.returnValue([
            {
                'name': d.name,
                'vendor': d.vendor,
                'model': d.model,
                'dev_type': d.dev_type
            } for d in result
        ])

    def scan(self, request):
        name = request.args.get('name', [])[0]
        deferred = self.service.getImage(name, request)
        finished = request.notifyFinish()

        def _finished(_):
            print('Request cancelled')
            deferred.cancel()

        def _cb(name):
            print('Process Finished: %s' % name)
            request.finish()

        def _eb(failure):
            if not isinstance(failure.value, CancelledError):
                request.finish()

        deferred.addCallbacks(_cb, _eb)
        finished.addErrback(_finished)
        return NOT_DONE_YET


registerAdapter(ScanResource, IScanService, IResource)