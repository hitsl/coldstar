# -*- coding: utf-8 -*-
import collections
import os
from pyinsane.abstract import get_devices
import time
from twisted.application.service import Service
from twisted.internet import defer, threads
from twisted.internet.error import ConnectionDone, ConnectionClosed, ProcessExitedAlready
from twisted.internet.interfaces import IPushProducer
from twisted.internet.protocol import ProcessProtocol, connectionDone
from twisted.protocols.basic import LineReceiver, LineOnlyReceiver
from zope.interface import implementer
from .interfaces import IScanService

__author__ = 'viruzzz-kun'


@implementer(IPushProducer)
class ScanProtocol(ProcessProtocol, LineReceiver):
    delimiter = '\n'

    def __init__(self, dev_name, consumer):
        self.process = None
        self.name = dev_name
        self.deferred = defer.Deferred(lambda w: self.stop())
        self.consumer = consumer

    def dataReceived(self, data):
        # if not hasattr(self.transport, 'disconnecting'):
        #     self.transport.disconnecting = False  # Dunno why
        return LineReceiver.dataReceived(self, data)

    def outReceived(self, data):
        return self.dataReceived(data)

    def lineReceived(self, line):
        print(line)
        if line.startswith('DATA'):
            self.setRawMode()

    def rawDataReceived(self, data):
        self.consumer.write(data)

    def processEnded(self, reason):
        """
        :type reason: twisted.python.failure.Failure
        :param reason:
        :return:
        """
        if self.deferred.called:
            return
        if isinstance(reason.value, ConnectionClosed):
            self.deferred.callback(self.name)
        else:
            self.deferred.errback(reason)

    def start(self):
        from twisted.internet import reactor
        self.process = reactor.spawnProcess(
            self,
            'python',
            ('python', os.path.join(os.path.dirname(__file__), 'worker.py'), self.name),
            env=None,
            childFDs={0: 'w', 1: 'r', 2: 2}
        )
        self.process.disconnecting = False

    def stop(self):
        try:
            self.process.signalProcess('INT')
        except (ProcessExitedAlready, OSError):
            pass


@implementer(IScanService)
class ScanService(Service):
    cache_timeout = 300

    def __init__(self):
        self.scan_queues = collections.defaultdict(list)
        self.scan_currents = {}
        self.scan_list_deferred = None
        self.cached_scan_list = ([], 0)

    def getImage(self, dev_name, consumer):
        protocol = ScanProtocol(dev_name, consumer)
        protocol.deferred.addBoth(self.promote, dev_name)
        self.scan_queues[dev_name].append(protocol)
        self.promote(dev_name)
        return protocol.deferred

    def getScanners(self, force=False):
        if self.scan_list_deferred:
            return self.scan_list_deferred

        if not force:
            l, deadline = self.cached_scan_list
            if deadline > time.time():
                return defer.succeed(l)

        def _cb(result):
            self.scan_list_deferred = None
            self.cached_scan_list = (result, time.time() + self.cache_timeout)
            return result

        def _eb(failure):
            self.scan_list_deferred = None
            self.cached_scan_list = ([], 0)
            return failure

        d = self.scan_list_deferred = threads.deferToThread(get_devices)
        d.addCallbacks(_cb, _eb)
        return d

    def promote(self, name):
        from twisted.internet import reactor

        c = self.scan_currents.get(name)
        if c is not None and c.name == name or c is None:
            n = self.scan_queues[name].pop(0)
            self.scan_currents[name] = n
            if n:
                reactor.callLater(0, n.start)