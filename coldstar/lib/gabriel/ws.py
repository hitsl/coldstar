# -*- coding: utf-8 -*-
import json

from autobahn.twisted.websocket import WebSocketServerFactory
from autobahn.twisted.websocket import WebSocketServerProtocol
from coldstar.lib.excs import SerializableBaseException, ExceptionWrapper
from coldstar.lib.utils import as_json
from .interfaces import IGabrielSession, IWebSocketProtocol
from twisted.internet import defer
from zope.interface import implementer


__author__ = 'viruzzz-kun'


@implementer(IWebSocketProtocol)
class WsProtocol(WebSocketServerProtocol):
    cookie_name = 'CastielAuthToken'
    user_id = None
    service = None
    cas = None
    session = None

    def __init__(self):
        self.cookies = {}

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

    def onClose(self, wasClean, code, reason):
        if self.session:
            self.session.unregister()
        WebSocketServerProtocol.onClose(self, wasClean, code, reason)

    def onConnect(self, request):
        """
        Обработчик соединения по WebSocket-протоколу. Нужен для того, чтобы вытащить печеньку 'CastielAuthToken'
        :param request: Request
        :type request: autobahn.websocket.protocol.ConnectionRequest
        :return:
        """
        self.session = IGabrielSession(self)
        self.session.session_manager = self.service
        self.processCookies(request)
        if self.cookie_name in self.cookies:
            token_hex = self.cookies.get(self.cookie_name)
            token = token_hex.decode('hex')
            if self.cas and token:
                o = self.cas.get_user_quick(token)
                self.user_id = o.user_id
                self.session.user_id = o.user_id
                self.session.register()
        return WebSocketServerProtocol.onConnect(self, request)

    def onMessage(self, payload, isBinary):
        WebSocketServerProtocol.onMessage(self, payload, isBinary)
        try:
            self.process_message(payload)
        except SerializableBaseException as e:
            self.sendMessageJson(e)
        except Exception as e:
            self.sendMessageJson(ExceptionWrapper(e))

    def process_message(self, payload):
        msg = json.loads(payload)
        msg_type = msg['type']
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

    @defer.inlineCallbacks
    def process_call(self, msg):
        uri = msg['uri']
        magic = msg['magic']
        args = msg.get('args', [])
        kwargs = msg.get('kwargs', {})

        result = yield self.session.received_call(uri, *args, **kwargs)
        self.sendMessageJson({
            'success': True,
            'magic': magic,
            'result': result,
        })

    def process_broadcast(self, msg):
        self.session.received_broadcast(uri=msg['uri'], data=msg['data'])

    def process_subscribe(self, msg):
        self.session.subscribe(msg['uri'])

    def process_unsubscribe(self, msg):
        self.session.unsubscribe(msg['uri'])

    def del_prefixed_subscriptions(self, uri):
        prefix = uri + '.'
        for k in self.subscriptions.keys():
            if k.startswith(prefix):
                del self.subscriptions[k]

    def sendMessageJson(self, obj):
        self.sendMessage(as_json(obj))

    def sendNotification(self, uri, data):
        self.sendMessageJson({'type': 'broadcast', 'uri': uri, 'data': data})


class WsFactory(WebSocketServerFactory):
    protocol = WsProtocol
    service = None
    cas = None

    def buildProtocol(self, addr):
        protocol = WebSocketServerFactory.buildProtocol(self, addr)
        protocol.service = self.service
        protocol.cas = self.cas
        return protocol


test_page = u"""Here be test page"""
