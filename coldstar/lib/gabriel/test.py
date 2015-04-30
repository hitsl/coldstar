# -*- coding: utf-8 -*-
import time
import blinker
import os

__author__ = 'viruzzz-kun'

boot_gabriel = blinker.signal('coldstar.lib.gabriel:boot')
broadcast_gabriel = blinker.signal('coldstar.lib.gabriel:broadcast')


class Test:
    def __init__(self):
        self.service = None
        boot_gabriel.connect(self.boot_gabriel)

    def echo(self, message):
        # Also broadcast through Service
        self.service.broadcast('test.echo', message)
        return message

    def data(self):
        data = {
            'id': 181,
            'roots': [100, 12, 32, 42],
            'dict': {
                'key': 'value',
                'random': os.urandom(8).encode('hex'),
            }
        }
        # Also broadcast through signal
        broadcast_gabriel.send(self, uri='test.data', data=data)
        return data

    def lc(self):
        self.service.broadcast('test.broadcast', {
            'test': 'test',
            'time': time.time()
        })

    def boot_gabriel(self, service):
        """
        :type service: coldstar.lib.gabriel.service.GabrielService
        :param service:
        :return:
        """
        print 'Gabriel Test: Service connected'
        self.service = service
        service.register_function('test.echo', self.echo)
        service.register_function('test.data', self.data)
        from twisted.internet.task import LoopingCall
        lc = LoopingCall(self.lc)
        lc.start(1)


def make(config):
    return Test()