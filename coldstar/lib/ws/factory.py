# -*- coding: utf-8 -*-
import logging
from autobahn.twisted.websocket import WebSocketServerFactory
from twisted.internet import defer
from .proto import WsProtocol
from .resource import WsTest

__author__ = 'viruzzz-kun'


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

    def bootstrap_test_functions(self):
        test_obj = WsTest()
        self.register_function('test', test_obj.echo)