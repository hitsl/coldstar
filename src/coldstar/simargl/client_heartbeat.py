# -*- coding: utf-8 -*-
import time

import blinker
from libsimargl.client import SimarglClient
from libsimargl.message import Message
from libcoldstar.utils import as_json
from twisted.internet.task import LoopingCall
from twisted.python.log import callWithContext

__author__ = 'viruzzz-kun'


class Client(SimarglClient):
    def startService(self):
        SimarglClient.startService(self)
        self.lc = LoopingCall(self.loop).start(10)

    def stopService(self):
        SimarglClient.stopService(self)
        if hasattr(self, 'lc'):
            self.lc.stop()

    def loop(self):
        message = Message()
        message.control = True
        message.uri = 'heartbeat'
        message.data = {'ts': time.time()}
        self.parent.dispatch_message(self, message=message)

