# -*- coding: utf-8 -*-
import blinker
from twisted.internet import defer
from twisted.internet.defer import CancelledError
from twisted.python.components import registerAdapter
from twisted.web.resource import Resource, IResource
from twisted.web.server import NOT_DONE_YET
from coldstar.application.scanner.interfaces import IScanService
from coldstar.lib.utils import api_method, get_args

__author__ = 'viruzzz-kun'


class ScanResource(Resource):
    isLeaf = 1

    def __init__(self, config):
        Resource.__init__(self)
        self.service = None
        self.cors_domain = config.get('cors_domain', '*')
        blinker.signal('coldstar:boot').connect(self.bootstrap)
        blinker.signal('coldstar.application.scanner:boot').connect(self.service_boot)
        blinker.signal('coldstar.lib.web:boot').connect(self.web_boot)

    def render(self, request):
        """
        :type request: coldstar.lib.web.wrappers.TemplatedRequest
        :param request:
        :return:
        """
        request.setHeader('Access-Control-Allow-Origin', self.cors_domain)
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
        defer.returnValue(result)

    def scan(self, request):
        j = get_args(request)
        name = j.get('name')
        options = {
            'format': j.get('format', 'png') or 'png',
            'resolution': str(j.get('resolution') or 300),
            'mode': j.get('mode') or 'Color'
        }
        if not name:
            request.setHeader('Content-Type', 'text/plain;charset=utf-8')
            request.setResponseCode(400)
            return 'Name should be set'
        deferred = self.service.getImage(name, request, options)
        finished = request.notifyFinish()

        def _finished(_):
            print('Request cancelled')
            deferred.cancel()

        def _cb(name):
            print('Process Finished: %s' % name)
            if not request._disconnected:
                request.finish()

        def _eb(failure):
            if not isinstance(failure.value, CancelledError):
                if not request._disconnected:
                    request.finish()

        deferred.addCallbacks(_cb, _eb)
        finished.addErrback(_finished)
        return NOT_DONE_YET

    def bootstrap(self, root):
        print('Scan Web: initialized')
        blinker.signal('coldstar.application.scanner.resource:boot').send(self)

    def service_boot(self, service):
        self.service = service
        print('Scan Web: ScanService connected')

    def web_boot(self, sender):
        sender.root_resource.putChild('scan', self)


registerAdapter(ScanResource, IScanService, IResource)


def make(config):
    return ScanResource(config)