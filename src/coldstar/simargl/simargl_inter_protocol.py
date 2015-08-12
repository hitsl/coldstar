# -*- coding: utf-8 -*-
import json
import struct

import blinker
from twisted.internet.protocol import Protocol, connectionDone, Factory

from libcoldstar import msgpack_helpers
from libcoldstar.utils import as_json
from libsimargl.message import Message

__author__ = 'viruzzz-kun'


header = struct.Struct('!Q')


class SimarglInterProtocol(Protocol):
    factory = None

    def __init__(self):
        self.buffer = b''
        self.mode = 'msgpack'
        self.q = []

    def dataReceived(self, data):
        self.buffer += data
        while 1:
            if len(self.buffer) < 8:
                return
            length, = header.unpack(self.buffer[:8])
            if len(self.buffer) < 8 + length:
                return
            buf, self.buffer = self.buffer[8:8 + length], self.buffer[8+length:]

            self.processData(buf)

    def processData(self, buf):
        if self.mode == 'negotiation':
            message = json.loads(buf)
            self.mode = message['mode']
            self._flush_q()
            return
        elif self.mode == 'json':
            data = json.loads(buf)
        elif self.mode == 'msgpack':
            data = msgpack_helpers.load(buf)
        else:
            return
        message = Message.from_json(data)

        self.factory.notify(message)

    def sendData(self, message):
        if self.mode == 'json':
            data = as_json(message)
        elif self.mode == 'msgpack':
            data = msgpack_helpers.dump(message.__json__())
        else:
            self.q.append(message)
            return
        self.transport.write(header.pack(len(data)))
        self.transport.write(data)

    def _flush_q(self):
        while self.q:
            self.sendData(self.q.pop(0))

    def connectionLost(self, reason=connectionDone):
        self.factory.unregisterProtocol(self)


class SimarglFactory(Factory):
    protocol = SimarglInterProtocol

    def __init__(self, service):
        self.service = service
        self.protocols = set()

    def buildProtocol(self, addr):
        p = self.protocol()
        p.factory = self
        self.protocols.add(p)
        return p

    def unregisterProtocol(self, p):
        self.protocols.remove(p)

    def send(self, message):
        for p in self.protocols:
            p.sendData(message)

    def notify(self,message):
        from twisted.internet import reactor
        reactor.callLater(0, blinker.signal('simargl.client:message').send, self.service, message=message)
