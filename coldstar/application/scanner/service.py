# -*- coding: utf-8 -*-
import collections
import os
from pyinsane.abstract import get_devices
from twisted.application.service import Service
from twisted.internet import defer
from twisted.internet.error import ConnectionDone, ConnectionClosed
from twisted.internet.interfaces import IPushProducer
from twisted.internet.protocol import ProcessProtocol, connectionDone
from twisted.protocols.basic import LineReceiver
from zope.interface import implementer
from .interfaces import IScanService

__author__ = 'viruzzz-kun'


@implementer(IPushProducer)
class ScanProtocol(ProcessProtocol, LineReceiver):
    consumer = None
    delimiter = '\n'

    def __init__(self, dev_name):
        self.busy = 0
        self.name = dev_name
        self.session_deferred = defer.Deferred()
        self.pause_buffer = []
        self.consumer = None

    def dataReceived(self, data):
        if self.paused:
            self.pause_buffer.append(data)
        else:
            if not hasattr(self.transport, 'disconnecting'):
                self.transport.disconnecting = False  # Dunno why
            return LineReceiver.dataReceived(self, data)

    def outReceived(self, data):
        return self.dataReceived(data)

    def lineReceived(self, line):
        print(line)
        if line.startswith('DATA'):
            self.setRawMode()

    def rawDataReceived(self, data):
        if self.consumer:
            self.consumer.write(data)

    def processEnded(self, reason):
        """
        :type reason: twisted.python.failure.Failure
        :param reason:
        :return:
        """
        if isinstance(reason.value, ConnectionClosed):
            self.session_deferred.callback(self.name)
        else:
            self.session_deferred.errback(reason)

    def start(self):
        from twisted.internet import reactor
        reactor.spawnProcess(
            self,
            'python',
            ('python', os.path.join(os.path.dirname(__file__), 'worker.py'), self.name),
            env=None,
            childFDs={0: 'w', 1: 'r', 2: 2}
        )

@implementer(IScanService)
class ScanService(Service):
    def __init__(self):
        self.scan_queues = collections.defaultdict(list)

    def getProducer(self, dev_name):
        protocol = ScanProtocol(dev_name)
        return defer.succeed(protocol)

    def getScanners(self):
        return defer.succeed(get_devices())
