# -*- coding: utf-8 -*-
from functools import partial
import json
from autobahn.twisted.resource import WebSocketResource
import blinker
from coldstar.lib.eventsource import make_event
from coldstar.lib.kalamari.test_page import TestPageResource
from coldstar.lib.kalamari.ws import WsFactory
from coldstar.lib.utils import api_method
from coldstar.lib.web.wrappers import Resource, AutoRedirectResource
from twisted.python.failure import Failure
from twisted.web import static
from twisted.web.server import NOT_DONE_YET

__author__ = 'viruzzz-kun'


boot = blinker.signal('coldstar.boot')
boot_web = blinker.signal('coldstar.lib.web.boot')
boot_cas = blinker.signal('coldstar.lib.castiel.boot')
boot_kalamari = blinker.signal('coldstar.lib.kalamari.boot')
boot_kalamari_web = blinker.signal('coldstar.lib.kalamari.webboot')


class KalamariFuncResource(Resource):
    isLeaf = 1
    service = None

    @api_method
    def render(self, request):
        """
        :type request: coldstar.lib.web.wrappers.TemplatedRequest
        :param request:
        :return:
        """
        pp = filter(None, request.postpath)
        if len(pp) != 1:
            request.setResponseCode(404)
            return ''
        uri = pp[0]
        if request.method == 'POST':
            j = json.loads(request.content)
            args = j.get('args', ())
            kwargs = j.get('kwargs', {})
        else:
            args = ()
            kwargs = dict(
                (key, value[0])
                for key, value in request.args.iteritems()
            )
        request.setHeader('Content-Type', 'application/json; charset=utf-8')
        return self.service.call(uri, *args, **kwargs)


class KalamariEventSourceResource(Resource):
    isLeaf = 1
    service = None

    def render(self, request):
        """
        :type request: coldstar.lib.web.wrappers.TemplatedRequest
        :param request:
        :return:
        """
        pp = filter(None, request.postpath)

        def push(uri, data):
            request.write(make_event(data, uri))

        def onFinish(result):
            self.service.unsubscribe(None, push)
            for uri, p in uri_dict.iteritems():
                self.service.unsubscribe(uri, p)
            if not isinstance(result, Failure):
                return result

        def register():
            if len(pp) == 1 and pp[0] == '*':
                self.service.subscribe(None, push)
            for uri, p in uri_dict.iteritems():
                self.service.subscribe(uri, p)

        uri_dict = dict(
            (uri, partial(push, uri))
            for uri in request.args.get('uri', [])
        )

        request.notifyFinish().addBoth(onFinish)

        register()
        request.setHeader('Content-Type', 'text/event-stream')
        request.write('')
        return NOT_DONE_YET


class KalamariResource(AutoRedirectResource):
    def __init__(self, config):
        AutoRedirectResource.__init__(self)
        self.service = None
        self.ws_factory = WsFactory()
        self.ws_resource = WebSocketResource(self.ws_factory)
        self.func_resource = KalamariFuncResource()
        self.es_resource = KalamariEventSourceResource()
        self.test_resource = TestPageResource()
        self.putChild('ws', self.ws_resource)
        self.putChild('exec', self.func_resource)
        self.putChild('eventsource', self.es_resource)
        self.putChild('test', self.test_resource)
        self.putChild('', static.Data(u'Kalamari (afrikaans) - это спрут'.encode('utf-8'), 'text/plain; charset=utf-8'))

        boot.connect(self.boot)
        boot_kalamari.connect(self.boot_kalamari)
        boot_web.connect(self.boot_web)
        boot_cas.connect(self.boot_cas)

    def boot(self, root):
        print 'Kalamari Web: boot...'
        boot_kalamari_web.send(self)

    def boot_web(self, web_service):
        web_service.root_resource.putChild('kalamari', self)
        print 'Kalamari Web: Connected to Web'

    def boot_kalamari(self, service):
        self.service = service
        self.func_resource.service = service
        self.es_resource.service = service
        self.ws_factory.service = service
        print 'Kalamari Web: Service connected'

    def boot_cas(self, castiel):
        print 'Kalamari WS: Cas connected'
        self.ws_factory.cas = castiel


def make(config):
    return KalamariResource(config)
