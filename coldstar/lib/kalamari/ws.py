# -*- coding: utf-8 -*-
from functools import partial
import json
from autobahn.twisted.resource import WebSocketResource

from autobahn.twisted.websocket import WebSocketServerFactory
import blinker
from autobahn.twisted.websocket import WebSocketServerProtocol
from coldstar.lib.utils import as_json
from coldstar.lib.web.wrappers import AutoRedirectResource
from twisted.web.static import Data


__author__ = 'viruzzz-kun'


class WsProtocol(WebSocketServerProtocol):
    cookie_name = 'CastielAuthToken'
    user_id = None
    service = None
    cas = None

    def __init__(self):
        self.cookies = {}
        self.subscriptions = {}

    def processCookies(self, request):
        for cookietxt in request.headers.get('cookie', []):
            if cookietxt:
                for cook in cookietxt.split(b';'):
                    cook = cook.lstrip()
                    try:
                        k, v = cook.split(b'=', 1)
                        self.cookies[k] = v
                    except ValueError:
                        pass

    def authenticate(self, token):
        if self.cas and token:
            o = self.cas.get_user_quick(token)
            self.user_id = o.user_id

    def onClose(self, wasClean, code, reason):
        for uri, p in self.subscriptions.iteritems():
            self.service.unsubscribe(uri, p)
            WebSocketServerProtocol.onClose(self, wasClean, code, reason)

    def onConnect(self, request):
        """
        Обработчик соединения по WebSocket-протоколу. Нужен для того, чтобы вытащить печеньку 'CastielAuthToken'
        :param request: Request
        :type request: autobahn.websocket.protocol.ConnectionRequest
        :return:
        """
        self.processCookies(request)
        if self.cookie_name in self.cookies:
            self.authenticate(self.cookies.get(self.cookie_name).decode('hex'))
        return WebSocketServerProtocol.onConnect(self, request)

    def onMessage(self, payload, isBinary):
        WebSocketServerProtocol.onMessage(self, payload, isBinary)
        msg = json.loads(payload)
        msg_type = msg['type']
        if msg_type == 'auth':  # В случае, если аутентифицируемся токеном вручную
            self.authenticate(msg['token'].decode('hex'))
        if not self.user_id:
            self.sendMessageJson({'exception': 'Not authorized', })
            return
        if msg_type == 'call':
            self.process_call(msg)
        elif msg_type == 'broadcast':
            self.process_broadcast(msg)
        elif msg_type == 'sub':
            self.process_subscribe(msg)
        elif msg_type == 'unsub':
            self.process_unsubscribe(msg)
        else:
            self.sendMessageJson({
                'exception': 'Unknown message type: %s' % msg_type,
                'object': msg,
            })

    def process_call(self, msg):
        uri = msg['uri']
        magic = msg['magic']
        args = msg.get('args', [])
        kwargs = msg.get('kwargs', {})

        def _cb(result):
            self.sendMessageJson({
                'magic': magic,
                'result': result,
            })

        def _eb(failure):
            self.sendMessageJson(failure.value)

        self.service.call(uri, *args, **kwargs).addCallbacks(_cb, _eb)

    def process_broadcast(self, msg):
        uri = msg['uri']
        data = msg['data']
        self.service.broadcast(uri=uri, data=data)

    def process_subscribe(self, msg):
        uri = msg['uri']
        if uri in self.subscriptions:
            return
        p = self.subscriptions[uri] = partial(self.sendNotification, uri)
        self.service.subscribe(uri, p)

    def process_unsubscribe(self, msg):
        uri = msg['uri']
        if uri in self.subscriptions:
            self.service.unsubscribe(uri, self.subscriptions.pop(uri))

    def del_prefixed_subscriptions(self, uri):
        prefix = uri + '.'
        for k in self.subscriptions.keys():
            if k.startswith(prefix):
                del self.subscriptions[k]

    def sendMessageJson(self, obj):
        self.sendMessage(as_json(obj))

    def sendNotification(self, uri, data):
        self.sendMessageJson({'uri': uri, 'data': data})


boot = blinker.signal('coldstar.boot')
boot_kalamari = blinker.signal('coldstar.lib.kalamari.boot')
boot_self = blinker.signal('coldstar.lib.kalamari.ws.boot')
boot_web = blinker.signal('coldstar.lib.web.boot')
boot_cas = blinker.signal('coldstar.lib.castiel.boot')


class WsFactory(WebSocketServerFactory):
    protocol = WsProtocol
    service = None
    cas = None

    def buildProtocol(self, addr):
        protocol = WebSocketServerFactory.buildProtocol(self, addr)
        protocol.service = self.service
        protocol.cas = self.cas
        return protocol


class WsResource(AutoRedirectResource):
    def __init__(self):
        AutoRedirectResource.__init__(self)
        self.ws_factory = WsFactory()
        self.putChild('', WebSocketResource(self.ws_factory))
        self.putChild('test', Data(test_page.encode('utf-8'), 'text/html; charset=utf-8'))
        boot.connect(self.boot)
        boot_kalamari.connect(self.boot_kalamari)
        boot_web.connect(self.boot_web)
        boot_cas.connect(self.boot_cas)

    def boot(self, root):
        print 'Kalamari WS: boot...'
        boot_self.send(self)

    def boot_kalamari(self, service):
        print 'Kalamari WS: Service connected'
        self.ws_factory.service = service

    def boot_web(self, web_service):
        print 'Kalamari WS: Web connected'
        web_service.root_resource.putChild('ws', self)

    def boot_cas(self, castiel):
        print 'Kalamari WS: Cas connected'
        self.ws_factory.cas = castiel

test_page = u"""Here be test page"""

def make(config):
    return WsResource()