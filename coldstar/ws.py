#!/usr/bin/env python
# -*- coding: utf-8 -*-
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory
import json
from twisted.python.components import registerAdapter
from zope.interface import Interface, implementer
from coldstar.interfaces import ILockService, ILockSession

__author__ = 'viruzzz-kun'
__created__ = '05.10.2014'


class IWsLockFactory(Interface):
    def register(self, client):
        pass

    def unregister(self, client):
        pass

    def acquire_lock(self, object_id, locker):
        pass

    def release_lock(self, object_id, token):
        pass


class WsLockProtocol(WebSocketServerProtocol):
    session = None

    def onOpen(self):
        self.factory.register(self)

    def onClose(self, wasClean, code, reason):
        WebSocketServerProtocol.onClose(self, wasClean, code, reason)
        if self.session:
            self.session.close()
        self.factory.unregister(self)

    def onMessage(self, payload, isBinary):
        WebSocketServerProtocol.onMessage(self, payload, isBinary)
        self.onMessageReceived(json.loads(payload))

    def onMessageReceived(self, msg):
        command = msg['command']

        if not self.session.locker:
            if command == 'locker':
                self.session.start_session(msg['locker'])
                self.sendMessageJson(True)
            else:
                self.sendMessageJson(False)
        else:
            if command == 'acquire_lock':
                token = self.session.acquire_lock(msg['object_id'])
                self.sendMessageJson(token)

            elif command == 'release_lock':
                result = self.session.release_lock(msg['object_id'])
                self.sendMessageJson(result)

            else:
                self.sendMessageJson(False)

    def sendMessageJson(self, obj):
        self.sendMessage(json.dumps(obj))


@implementer(IWsLockFactory)
class WsLockFactory(WebSocketServerFactory):
    protocol = WsLockProtocol

    def __init__(self, service):
        """
        :type service: coldstar.service.ColdStarService
        :param service:
        :return:
        """
        WebSocketServerFactory.__init__(self)
        self.service = service
        self.clients = []

    def register(self, client):
        """
        :type client: WsLockProtocol
        :param client:
        :return:
        """
        self.clients.append(client)

    def unregister(self, client):
        """
        :type client: WsLockProtocol
        :param client:
        :return:
        """
        if client in self.clients:
            self.clients.remove(client)

    def acquire_lock(self, object_id, locker):
        return self.service.acquire_lock(object_id, locker)

    def release_lock(self, object_id, token):
        return self.service.release_lock(object_id, token)

    def buildProtocol(self, addr):
        protocol = self.protocol()
        protocol.factory = self
        protocol.session = ILockSession(self.service)
        return protocol


registerAdapter(WsLockFactory, ILockService, IWsLockFactory)