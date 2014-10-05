#!/usr/bin/env python
# -*- coding: utf-8 -*-
from twisted.web.server import Site

from coldstar.service import ColdStarService
from coldstar.rest import RestService
from twisted.application import internet
from twisted.application.service import Application

__author__ = 'viruzzz-kun'
__created__ = '05.10.2014'


application = Application('Coldstar')

cold_star = ColdStarService()
cold_star.setServiceParent(application)

rest_service = RestService(cold_star)
rest_resource = rest_service.app.resource()

# root_resource = Resource()
# root_resource.putChild('/', rest_resource)

site = Site(rest_resource)

web_service = internet.TCPServer(5000, site, interface='0.0.0.0')
web_service.setServiceParent(application)
