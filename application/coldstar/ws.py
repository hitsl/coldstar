#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import json

from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory
from twisted.python.components import registerAdapter
from zope.interface import implementer

from lib.excs import MethodNotFoundException, SerializableBaseException, ExceptionWrapper, BadRequest
from .interfaces import ILockService, ILockSession, ISessionLockProtocol, IWsLockFactory
from lib.utils import as_json


__author__ = 'viruzzz-kun'
__created__ = '05.10.2014'


logging.getLogger().setLevel(logging.DEBUG)


@implementer(ISessionLockProtocol)
class WsLockProtocol(WebSocketServerProtocol):
    session = None

    def onOpen(self):
        self.factory.register(self)

    def onClose(self, wasClean, code, reason):
        WebSocketServerProtocol.onClose(self, wasClean, code, reason)
        if self.session:
            self.session.close_session()
        self.factory.unregister(self)

    def onMessage(self, payload, isBinary):
        WebSocketServerProtocol.onMessage(self, payload, isBinary)
        msg = json.loads(payload)
        logging.info('message: %s', msg)
        try:
            result = self.onMessageReceived(msg)
        except SerializableBaseException, e:
            self.sendMessage(as_json({
                'magic': msg.get('magic', 'magic'),
                'exception': e,
            }))
        except Exception, e:
            self.sendMessage(as_json({
                'magic': msg.get('magic', 'magic'),
                'exception': ExceptionWrapper(e),
            }))
        else:
            self.sendMessage(as_json({
                'result': result,
                'magic': msg.get('magic', 'magic')
            }))

    def onMessageReceived(self, msg):
        command = msg.get('command', None)
        params = msg.get('params', None)
        if not isinstance(command, (str, unicode)):
            raise BadRequest
        method = getattr(self, 'command_' + command, None)
        if method is None:
            raise MethodNotFoundException(command)
        return method(params)

    def sendMessageJson(self, obj):
        self.sendMessage(as_json(obj))

    # ISessionLockProtocol interface

    def command_locker(self, params):
        return self.session.start_session(params['locker'])

    def command_acquire_lock(self, params):
        return self.session.acquire_lock(params['object_id'])

    def command_release_lock(self, params):
        return self.session.release_lock(params['object_id'])


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
        logging.info('Connection from %s', client.peer)
        self.clients.append(client)

    def unregister(self, client):
        """
        :type client: WsLockProtocol
        :param client:
        :return:
        """
        if client in self.clients:
            self.clients.remove(client)
            logging.info('Client %s disconnected', client.peer)

    def buildProtocol(self, addr):
        protocol = self.protocol()
        protocol.factory = self
        protocol.session = ILockSession(self.service)
        return protocol


registerAdapter(WsLockFactory, ILockService, IWsLockFactory)