# -*- coding: utf-8 -*-
from coldstar.ws.factory import WsFactory
from coldstar.ws.resource import WsResource
from libcoldstar.plugin_helpers import ColdstarPlugin, Dependency

__author__ = 'viruzzz-kun'


class WsService(ColdstarPlugin):
    signal_name = 'coldstar.ws'
    web = Dependency('libcoldstar.web')

    def __init__(self, config):
        self.config = config

    @web.on
    def web_boot(self, web):
        factory = WsFactory(self)
        resource = WsResource(factory)
        web.root_resource.putChild('ws', resource)
