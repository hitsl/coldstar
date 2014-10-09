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
    def register(self, client):
        pass

    def unregister(self, client):
        pass

    def acquire_lock(self, object_id, locker):
        pass

    def release_lock(self, object_id, token):
        pass


class WsLockProtocol(WebSocketServerProtocol):
    def __init__(self):
        self.locks = {}
        self.locker = None

    def onOpen(self):
        self.factory.register(self)

    def onClose(self, wasClean, code, reason):
        WebSocketServerProtocol.onClose(self, wasClean, code, reason)
        if self.locks:
            for object_id, lock in self.locks.iteritems():
                self.factory.release_lock(object_id, lock.token)
        self.factory.unregister(self)

    def onMessage(self, payload, isBinary):
        self.onMessageReceived(json.loads(payload))

    def onMessageReceived(self, msg):
        command = msg['command']

        if command == 'acquire_lock':
            token = self.command_acquire_lock(msg['object_id'])
            self.sendMessageJson(token)

        elif command == 'release_lock':
            result = self.command_release_lock(msg['object_id'], msg['token'])
            self.sendMessageJson(result)

        elif command == 'locker':
            if not self.locker:
                self.locker = msg['locker']
                self.sendMessageJson(True)
            else:
                self.sendMessageJson(False)

    def sendMessageJson(self, obj):
        self.sendMessage(json.dumps(obj))

    def command_acquire_lock(self, object_id):
        if not self.locker:
            return False
        if object_id in self.locks:
            return False
        return self.factory.acquire_lock(object_id, self.locker)

    def command_release_lock(self, object_id, token):
        result = self.factory.release_lock(object_id, token)
        self.locks.pop(object_id)
        return result


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