#!/usr/bin/env python
# -*- coding: utf-8 -*-
from autobahn.twisted.resource import WebSocketResource
from twisted.application import internet
from twisted.web.resource import IResource
from twisted.web.server import Site
from coldstar.rest import IRestService
from coldstar.service import ColdStarService
from coldstar.ws import IWsLockFactory

__author__ = 'viruzzz-kun'
__created__ = '13.09.2014'


def makeService(config):
    cold_star = ColdStarService()
    cold_star.short_timeout = int(config.get('tmp-lock-timeout', 60))
    cold_star.long_timeout = int(config.get('lock-timeout', 3600))

    rest_service = IRestService(cold_star)
    rest_resource = IResource(rest_service)

    if config.get('web-sockets'):
        ws_factory = IWsLockFactory(cold_star)
        ws_resource = WebSocketResource(ws_factory)
        # noinspection PyArgumentList
        rest_resource.putChild('ws', ws_resource)

    site = Site(rest_resource)

    web_service = internet.TCPServer(
        int(config.get('port', 5000)),
        site,
        interface=config.get('interface', '0.0.0.0')
    )
    web_service.setServiceParent(cold_star)

    return cold_star
