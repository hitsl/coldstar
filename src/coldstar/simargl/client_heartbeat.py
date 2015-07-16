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
        LoopingCall(self.loop).start(10)

    def loop(self):
        message = Message()
        message.control = True
        message.topic = 'heartbeat'
        message.data = {'ts': time.time()}
        blinker.signal('simargl.client:message').send(self, message=message)

