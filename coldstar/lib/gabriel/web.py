# -*- coding: utf-8 -*-
from functools import partial
import json
from autobahn.twisted.resource import WebSocketResource
import blinker
from coldstar.lib.eventsource import make_event
from coldstar.lib.gabriel.interfaces import IGabrielSession
from coldstar.lib.gabriel.test_page import TestPageResource
from coldstar.lib.gabriel.ws import WsFactory
from coldstar.lib.utils import api_method
from coldstar.lib.web.wrappers import Resource, AutoRedirectResource
from twisted.python.failure import Failure
from twisted.web import static
from twisted.web.server import NOT_DONE_YET

__author__ = 'viruzzz-kun'


boot = blinker.signal('coldstar:boot')
boot_web = blinker.signal('coldstar.lib.web:boot')
boot_cas = blinker.signal('coldstar.lib.castiel:boot')
boot_gabriel = blinker.signal('coldstar.lib.gabriel:boot')
boot_gabriel_web = blinker.signal('coldstar.lib.gabriel.webboot')


class GabrielFuncResource(Resource):
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


class GabrielEventSourceResource(Resource):
    isLeaf = 1
    service = None

    def render(self, request):
        """
        :type request: coldstar.lib.web.wrappers.TemplatedRequest
        :param request:
        :return:
        """
        user = request.get_auth()
        if not user:
            request.setResponseCode(401)
            return ''
        session = IGabrielSession(request)
        session.session_manager = self.service
        session.user_id = user.user_id

        for uri in request.args.get('uri'):
            session.subscribe(uri)

        def onFinish(result):
            session.unregister()
            if not isinstance(result, Failure):
                return result

        request.notifyFinish().addBoth(onFinish)
        request.setHeader('Content-Type', 'text/event-stream')
        request.write('')
        session.register()
        return NOT_DONE_YET


class GabrielResource(AutoRedirectResource):
    def __init__(self, config):
        AutoRedirectResource.__init__(self)
        self.service = None
        self.ws_factory = WsFactory()
        self.ws_resource = WebSocketResource(self.ws_factory)
        self.func_resource = GabrielFuncResource()
        self.es_resource = GabrielEventSourceResource()
        self.test_resource = TestPageResource()
        self.putChild('ws', self.ws_resource)
        self.putChild('exec', self.func_resource)
        self.putChild('eventsource', self.es_resource)
        self.putChild('test', self.test_resource)
        self.putChild('', static.Data(u'I am Gabriel, trickster Loki'.encode('utf-8'), 'text/plain; charset=utf-8'))

        boot.connect(self.boot)
        boot_gabriel.connect(self.boot_gabriel)
        boot_web.connect(self.boot_web)
        boot_cas.connect(self.boot_cas)

    def boot(self, root):
        print 'Gabriel Web: boot...'
        boot_gabriel_web.send(self)

    def boot_web(self, web_service):
        web_service.root_resource.putChild('gabriel', self)
        print 'Gabriel Web: Connected to Web'

    def boot_gabriel(self, service):
        self.service = service
        self.func_resource.service = service
        self.es_resource.service = service
        self.ws_factory.service = service
        print 'Gabriel Web: Service connected'

    def boot_cas(self, castiel):
        print 'Gabriel WS: Cas connected'
        self.ws_factory.cas = castiel


def make(config):
    return GabrielResource(config)
