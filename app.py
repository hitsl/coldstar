#!/usr/bin/env python
# -*- coding: utf-8 -*-
from autobahn.twisted.resource import WebSocketResource
from twisted.web.resource import IResource
from twisted.web.server import Site
from twisted.application import internet, service

from coldstar.service import ColdStarService
from coldstar.rest import IRestService
from coldstar.ws import IWsLockFactory


__author__ = 'viruzzz-kun'
__created__ = '05.10.2014'


application = service.Application('ColdStar')

cold_star = ColdStarService()
cold_star.setServiceParent(application)

rest_service = IRestService(cold_star)
rest_resource = IResource(rest_service)

ws_factory = IWsLockFactory(cold_star)
ws_resource = WebSocketResource(ws_factory)

rest_resource.putChild('ws', ws_resource)

site = Site(rest_resource)

web_service = internet.TCPServer(5000, site, interface='0.0.0.0')
web_service.setServiceParent(application)
