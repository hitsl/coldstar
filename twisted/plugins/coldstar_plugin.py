#!/usr/bin/env python
# -*- coding: utf-8 -*-

from zope.interface import implementer

from twisted.python import usage
from twisted.application.service import IServiceMaker
from twisted.plugin import IPlugin

__author__ = 'viruzzz-kun'
__created__ = '13.09.2014'


class Options(usage.Options):
    synopsis = "[options]"
    longdesc = "Make a ColdStar server."
    optParameters = [
        ['port', 'p', 5000, 'Port to listen on for HTTP and WebSocket requests'],
        ['interface', 'i', '0.0.0.0', 'Interface to bind to'],
        ['tmp-lock-timeout', None, 60, 'Timeout for temporary locks'],
        ['lock-timeout', None, 3600, 'Timeout for permanent locks'],
        ['db-url', None, 'mysql+cymysql://127.0.0.1/hospital']
    ]

    optFlags = [['web-sockets', 'w', 'Use WebSockets']]


@implementer(IServiceMaker, IPlugin)
class MyServiceMaker(object):
    tapname = "coldstar"
    description = "ColdStar notification and locking server."
    options = Options

    def makeService(self, config):
        import application.bootstrap
        return application.bootstrap.RootService(config)



serviceMaker = MyServiceMaker()