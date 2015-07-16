# -*- coding: utf-8 -*-
import time

import blinker
from libsimargl.client import SimarglClient
from libsimargl.message import Message
from libcoldstar.utils import as_json
from twisted.internet.task import LoopingCall
from twisted.python import log
from twisted.python.log import callWithContext

__author__ = 'viruzzz-kun'


class Client(SimarglClient):
    def startService(self):
        SimarglClient.startService(self)

    def send(self, message):
        if message.topic != 'heartbeat':
            log.msg(as_json(message), system='SimarglPrintClient')

