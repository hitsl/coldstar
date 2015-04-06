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
        ['config', 'c', None, 'Configuration file'],
    ]
    optFlags = []


@implementer(IServiceMaker, IPlugin)
class MyServiceMaker(object):
    tapname = "coldstar"
    description = "ColdStar notification and locking server."
    options = Options

    def makeService(self, config):
        from coldstar.lib.pluginmanager.service import Application
        return Application(config)


serviceMaker = MyServiceMaker()