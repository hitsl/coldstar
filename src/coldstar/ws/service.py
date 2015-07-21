# -*- coding: utf-8 -*-
from twisted.application.service import Service
from coldstar.ws.factory import WsFactory
from coldstar.ws.resource import WsResource
from libcoldstar.plugin_helpers import ColdstarPlugin, Dependency

__author__ = 'viruzzz-kun'


class WsService(Service, ColdstarPlugin):
    signal_name = 'coldstar.ws'
    web = Dependency('libcoldstar.web')
    simargl = Dependency('coldstar.simargl', optional=True)

    def __init__(self, config):
        self.config = config
        self.factory = WsFactory(self)
        self.resource = WsResource(self.factory)

        self.register_function = self.factory.register_function
        self.unregister_function = self.factory.unregister_function
        self.broadcast = self.factory.broadcast

    @web.on
    def web_boot(self, web):
        web.root_resource.putChild('ws', self.resource)

    def send(self, message):
        self.factory.broadcast(message)

    def dispatch_message(self, message):
        self.simargl.dispatch_message(self, message)

    @simargl.on
    def on_simargl(self, simargl):
        simargl.clients[self.name] = self
