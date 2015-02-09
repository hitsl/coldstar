# -*- coding: utf-8 -*-
import logging
import blinker
from itsdangerous import json
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory
from twisted.internet import defer
from coldstar.lib.utils import as_json

__author__ = 'viruzzz-kun'


class WsProtocol(WebSocketServerProtocol):
    cookie_name = 'CastielAuthToken'
    broadcast_signal = blinker.signal('websocket.broadcast')
    session = None
    factory = None
    token = None

    def __init__(self):
        self.cookies = {}
        self.subscriptions = {}

    def onConnect(self, request):
        """
        Обработчик соединения по WebSocket-протоколу. Нужен для того, чтобы вытащить печеньку 'CastielAuthToken'
        :param request: Request
        :type request: autobahn.websocket.protocol.ConnectionRequest
        :return:
        """
        cookieheaders = request.headers.get('cookie')
        if cookieheaders is not None:
            for cookietxt in cookieheaders:
                if cookietxt:
                    for cook in cookietxt.split(b';'):
                        cook = cook.lstrip()
                        try:
                            k, v = cook.split(b'=', 1)
                            self.received_cookies[k] = v
                        except ValueError:
                            pass
        self.token = self.cookies.get(self.cookie_name)
        return WebSocketServerProtocol.onConnect(self, request)

    def onOpen(self):
        self.factory.register_client(self)
        return WebSocketServerProtocol.onOpen(self)

    def onClose(self, wasClean, code, reason):
        if self.session:
            self.session.close_session()
        self.factory.unregister_client(self)
        return WebSocketServerProtocol.onClose(self, wasClean, code, reason)

    def onMessage(self, payload, isBinary):
        WebSocketServerProtocol.onMessage(self, payload, isBinary)
        msg = json.loads(payload)
        msg_type = msg['type']
        if msg_type == 'auth':  # В случае, если аутентифицируемся токеном вручную
            self.token = msg['token']
        if not self.token:
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

        d = self.factory.remote_call(uri, args, kwargs)
        d.addCallbacks(_cb, _eb)

    def process_broadcast(self, msg):
        uri = msg['uri']
        data = msg['data']
        self.broadcast_signal.send(self, uri=uri, data=data)

    def process_subscribe(self, msg):
        uri = msg['uri']
        if uri in self.subscriptions:
            return
        self.del_prefixed_subscriptions(uri)
        self.subscriptions[uri] = 1

    def process_ubsubscribe(self, msg):
        uri = msg['uri']
        if uri in self.subscriptions:
            del self.subscriptions[uri]
        self.del_prefixed_subscriptions(uri)

    @broadcast_signal.connect
    def broadcast(self, sender, **kwargs):
        if sender is self:
            return
        uri = kwargs['uri']
        path = uri.split('.')
        process = False
        while not process and path:
            process = '.'.join(path) in self.subscriptions
            path.pop()

        if process:
            self.sendMessageJson({
                'uri': uri,
                'data': kwargs['data'],
            })

    def del_prefixed_subscriptions(self, uri):
        prefix = uri + '.'
        for k in self.subscriptions.keys():
            if k.startswith(prefix):
                del self.subscriptions[k]

    def sendMessageJson(self, obj):
        self.sendMessage(as_json(obj))


class WsFactory(WebSocketServerFactory):
    protocol = WsProtocol

    def __init__(self, service):
        """
        :type service: coldstar.service.ColdStarService
        :param service:
        :return:
        """
        WebSocketServerFactory.__init__(self)
        self.service = service
        self.clients = []
        self.functions = {}

    def register_client(self, client):
        """
        :type client: WsProtocol
        :param client:
        :return:
        """
        logging.info('Connection from %s', client.peer)
        self.clients.append(client)

    def unregister_client(self, client):
        """
        :type client: WsProtocol
        :param client:
        :return:
        """
        if client in self.clients:
            self.clients.remove(client)
            logging.info('Client %s disconnected', client.peer)

    def register_function(self, uri, function):
        if uri in self.functions:
            raise RuntimeError(u'URI "%s" already taken' % uri)
        self.functions[uri] = function

    def unregister_function(self, uri):
        del self.functions[uri]

    def remote_call(self, uri, args, kwargs):
        if uri not in self.functions:
            return defer.fail(RuntimeError('URI "%s" is not registered' % uri))
        function = self.functions[uri]
        return defer.maybeDeferred(function, *args, **kwargs)

    def buildProtocol(self, addr):
        protocol = self.protocol()
        protocol.factory = self
        # protocol.session = ILockSession(self.service)
        return protocol

