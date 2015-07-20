# -*- coding: utf-8 -*-
import fnmatch
import functools
import json

import blinker
from autobahn.twisted.websocket import WebSocketServerProtocol
import itertools
from twisted.python import log
from libcoldstar.api_helpers import as_json


__author__ = 'viruzzz-kun'


class WsProtocol(WebSocketServerProtocol):
    cookie_name = 'CastielAuthToken'
    broadcast_signal = blinker.signal('websocket.broadcast')
    session = None
    factory = None
    token = None

    def __init__(self):
        self.cookies = {}
        self.subscriptions = set()

    def process_cookies(self, request):
        self.cookies = {}
        cookie_headers = request.headers.get('cookie')
        if not cookie_headers:
            return
        for cook in itertools.imap(unicode.lstrip, cookie_headers.split(b';')):
            try:
                k, v = cook.split(b'=', 1)
                self.cookies[k] = v
            except ValueError:
                pass

    def onConnect(self, request):
        """
        Обработчик соединения по WebSocket-протоколу. Нужен для того, чтобы вытащить печеньку 'CastielAuthToken'
        :param request: Request
        :type request: autobahn.websocket.protocol.ConnectionRequest
        :return:
        """
        log.msg('Achtung! Connection! %s', request.peer)
        self.process_cookies(request)
        self.token = self.cookies.get(self.cookie_name)
        return WebSocketServerProtocol.onConnect(self, request)

    def onOpen(self):
        log.msg('Achtung! Open!')
        self.factory.register_client(self)
        return WebSocketServerProtocol.onOpen(self)

    def onClose(self, wasClean, code, reason):
        if self.session:
            self.session.close_session()
        self.factory.unregister_client(self)
        return WebSocketServerProtocol.onClose(self, wasClean, code, reason)

    def onMessage(self, payload, isBinary):
        WebSocketServerProtocol.onMessage(self, payload, isBinary)
        if not isBinary:
            payload = payload.decode('string_escape')
        log.msg(payload, system="WebSocket DEBUG")
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
        self.factory.broadcast(uri, data, self)

    def process_subscribe(self, msg):
        uri = msg['uri']
        self.subscriptions.add(uri)

    def process_ubsubscribe(self, msg):
        uri = msg['uri']
        self.subscriptions.remove(uri)

    def broadcast(self, uri, data):
        match_fn = functools.partial(fnmatch.fnmatch, uri)
        match_iter = itertools.imap(match_fn, self.subscriptions)
        if any(match_iter):
            self.sendMessageJson({
                'uri': uri,
                'data': data,
            })

    def sendMessageJson(self, obj):
        self.sendMessage(as_json(obj))
