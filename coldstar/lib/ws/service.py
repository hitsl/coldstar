# -*- coding: utf-8 -*-
import logging

from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory
from itsdangerous import json
from twisted.internet import defer
from zope.interface import implementer

from coldstar.lib.registry import Registry
from coldstar.lib.utils import as_json
from .interfaces import IWSService, IPubSubService, IRPCService

__author__ = 'viruzzz-kun'


class WsRoutingProtocol(WebSocketServerProtocol):
    session = None
    factory = None

    def __init__(self):
        WebSocketServerProtocol.__init__(self)
        self.subscriptions = set()

    def onOpen(self):
        self.factory.register_client(self)

    def onClose(self, wasClean, code, reason):
        WebSocketServerProtocol.onClose(self, wasClean, code, reason)
        if self.session:
            self.session.close_session()
        self.factory.unregister_client(self)

    def onMessage(self, payload, isBinary):
        WebSocketServerProtocol.onMessage(self, payload, isBinary)
        self.factory.dispatch_message(self, json.loads(payload))

    def sendMessageJson(self, obj):
        self.sendMessage(as_json(obj))


@implementer(IWSService, IPubSubService, IRPCService)
class WsRoutingFactory(WebSocketServerFactory):
    protocol = WsRoutingProtocol

    def __init__(self):
        WebSocketServerFactory.__init__(self)
        self.clients = []
        self.rpc_registry = Registry()
        self.subscription_registry = Registry()
        self.client_registry = {}

    def register_client(self, client):
        logging.info('Connection from %s', client.peer)
        self.clients.append(client)

    def unregister_client(self, client):
        if client in self.clients:
            self.clients.remove(client)
            logging.info('Client %s disconnected', client.peer)

    @defer.inlineCallbacks
    def dispatch_message(self, client, msg):
        """
        :type client: WsRoutingProtocol
        :type msg: dict
        :param client:
        :param msg:
        :return:
        """
        import traceback

        uri = msg['uri']
        t = msg['type']
        if t == 'call':
            try:
                result = yield self.rpc_registry[uri].value(*msg['args'])
            except KeyError:
                client.sendMessageJson({
                    'uri': uri,
                    'magic': msg['magic'],
                    'exception': {

                    }
                })
            except:
                traceback.print_exc()
            else:
                client.sendMessageJson({
                    'uri': uri,
                    'magic': msg['magic'],
                    'result': result,
                })

        elif t == 'broadcast':
            try:
                clients_result = set()
                for key, clients in self.subscription_registry.super_tree(uri).iteritems():
                    if not clients:
                        continue
                    clients_result.update(clients)
            except:
                traceback.print_exc()
            else:
                message = as_json({
                    'uri': uri,
                    'data': msg['data'],
                    })
                for c in clients_result:
                    c.sendMessage(message)

        elif t == 'subscribe':
            client.subscriptions.add(uri)
            self.rebuild_subscription_registry()

        elif t == 'unsubscribe':
            client.subscriptions.pop(uri, None)
            self.rebuild_subscription_registry()

    def rebuild_subscription_registry(self):
        br = self.subscription_registry = Registry()
        for client in self.clients:
            for uri in client.subsctiptions:
                br[uri] = client

    def buildProtocol(self, addr):
        protocol = self.protocol()
        protocol.factory = self
        return protocol