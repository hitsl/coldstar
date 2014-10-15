#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'viruzzz-kun'
__created__ = '13.09.2014'


def makeService(config):
    from autobahn.twisted.resource import WebSocketResource
    from twisted.application import internet
    from twisted.web.resource import IResource, Resource
    from twisted.web.server import Site
    from coldstar.interfaces import IRestService, IWsLockFactory

    from coldstar.service import ColdStarService
    from coldstar.test_page import TestPageResource

    from coldstar import rest, ws, session

    cold_star = ColdStarService()
    cold_star.short_timeout = int(config.get('tmp-lock-timeout', 60))
    cold_star.long_timeout = int(config.get('lock-timeout', 3600))

    rest_service = IRestService(cold_star)
    rest_resource = IResource(rest_service)

    ws_factory = IWsLockFactory(cold_star)
    ws_resource = WebSocketResource(ws_factory)

    test_page_resource = TestPageResource()

    root_resource = Resource()
    root_resource.putChild('lock', rest_resource)
    root_resource.putChild('ws', ws_resource)
    root_resource.putChild('test', test_page_resource)

    site = Site(root_resource)

    web_service = internet.TCPServer(
        int(config.get('port', 5000)),
        site,
        interface=config.get('interface', '0.0.0.0')
    )
    web_service.setServiceParent(cold_star)

    return cold_star
