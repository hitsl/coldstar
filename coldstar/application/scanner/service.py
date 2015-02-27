# -*- coding: utf-8 -*-
import collections
import os
from pyinsane.abstract import get_devices
from twisted.application.service import Service
from twisted.internet import defer
from twisted.internet.interfaces import IPushProducer
from twisted.internet.protocol import ProcessProtocol, connectionDone
from twisted.protocols.basic import LineReceiver
from zope.interface import implementer
from coldstar.application.scanner.interfaces import IScanService

__author__ = 'viruzzz-kun'


@implementer(IPushProducer)
class ScanProtocol(ProcessProtocol, LineReceiver):
    consumer = None

    def __init__(self, dev_name):
        self.busy = 0
        self.name = dev_name
        self.session_deferred = defer.Deferred()

    def outReceived(self, data):
        return self.dataReceived(data)

    def lineReceived(self, line):
        if line == 'DATA':
            self.setRawMode()

    def rawDataReceived(self, data):
        self.consumer.write(data)

    def connectionLost(self, reason=connectionDone):
        if reason == connectionDone:
            self.session_deferred.callback(self.name)
        else:
            self.session_deferred.errback(reason)


@implementer(IScanService)
class ScanService(Service):
    def __init__(self):
        Service.__init__(self)
        self.scan_queues = collections.defaultdict(list)

    def getProducer(self, dev_name):
        from twisted.internet import reactor

        protocol = ScanProtocol(dev_name)
        reactor.spawnProcess(
            protocol,
            'python',
            (os.path.join(os.path.dirname(__file__), 'worker.py'), protocol.name),
            env=None,
            childFDs={0: 'w', 1: 'r', 2: 2}
        )

        return defer.succeed(protocol)

    def getScanners(self):
        return defer.succeed(get_devices())
