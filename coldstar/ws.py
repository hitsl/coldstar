#!/usr/bin/env python
# -*- coding: utf-8 -*-
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory
import json
from twisted.python.components import registerAdapter
from zope.interface import Interface, implementer
from coldstar.interfaces import IColdStarService

__author__ = 'viruzzz-kun'
__created__ = '05.10.2014'


class IWsLockFactory(Interface):
    def acquire_lock(self, object_id, locker):
        pass

    def release_lock(self, object_id, token):
        pass


class WsLockProtocol(WebSocketServerProtocol):
    def __init__(self):
        self.lock = None
        self.locker = None

    def onOpen(self):
        self.factory.register(self)

    def onClose(self, wasClean, code, reason):
        WebSocketServerProtocol.onClose(self, wasClean, code, reason)
        if self.lock:
            self.factory.release_lock(self.lock.object_id, self.lock.token)
        self.factory.unregister(self)

    def onMessage(self, payload, isBinary):
        self.onMessageReceived(json.loads(payload))

    def onMessageReceived(self, msg):
        command = msg['command']
        if command == 'acquire_lock':
            self.sendMessageJson(self.command_acquire_lock(msg['object_id']))
        elif command == 'release_lock':
            self.sendMessageJson(self.command_release_lock(msg['object_id'], msg['token']))
        elif command == 'locker':
            self.locker = msg['locker']

    def sendMessageJson(self, obj):
        self.sendMessage(json.dumps(obj))

    def command_acquire_lock(self, object_id):
        if not self.locker:
            return False
        if self.lock:
            return False
        self.sendMessageJson(self.factory.acquire_lock(object_id, self.locker))

    def command_release_lock(self, object_id, token):
        self.sendMessageJson(self.factory.release_lock(object_id, token))


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
        self.clients.remove(client)

    def acquire_lock(self, object_id, locker):
        return self.service.acquire_lock(object_id, locker)

    def release_lock(self, object_id, token):
        return self.service.release_lock(object_id, token)


registerAdapter(WsLockFactory, IColdStarService, IWsLockFactory)