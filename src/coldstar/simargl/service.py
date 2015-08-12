# -*- coding: utf-8 -*-
import ConfigParser
import uuid
from twisted.python import log

from libcoldstar.plugin_helpers import connect_to_signal, ColdstarPlugin, Dependency
from twisted.application.service import MultiService

__author__ = 'viruzzz-kun'


class Simargl(MultiService, ColdstarPlugin):
    signal_name = 'coldstar.simargl'
    root = Dependency('coldstar')
    name = 'Simargl.Service'

    def __init__(self, config):
        MultiService.__init__(self)
        self.uuid = uuid.uuid4()
        self.clients = {}
        with open(config['config'], 'rt') as fp:
            parsed_config = ConfigParser.ConfigParser()
            parsed_config.readfp(fp)

        for name in parsed_config.sections():
            mod_name = parsed_config.get(name, 'module')
            module = __import__(mod_name, globals(), locals(), fromlist=['Client'])
            client = getattr(module, 'Client')(dict(parsed_config.items(name)))
            client.setName(name)
            client.setServiceParent(self)
            self.clients[name] = client

    @connect_to_signal('simargl.client:message')
    def message_received(self, client, message):
        """
        Зднсь должен происходить некоторый роутинг
        :type client: coldstar.simargl.client.SimarglClient
        :type message: coldstar.simargl.message.Message
        :param client:
        :param message:
        :return:
        """
        name = client.name
        if client is not self.clients.get(name):
            log.msg('Name mismatch', system="Simargl")
            return
        if self.uuid.bytes in message.hops:
            # log.msg('Short circuit detected', system="Simargl")
            return
        message.hops.append(self.uuid.bytes)
        for recipient in self.clients.itervalues():
            recipient.send(message)
