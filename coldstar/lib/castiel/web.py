#!/usr/bin/env python
# -*- coding: utf-8 -*-
import blinker
from twisted.web.resource import IResource, Resource
from twisted.web.static import Data

from zope.interface import implementer
from coldstar.lib.castiel.rpc import CastielApiResource
from coldstar.lib.castiel.user_login import CastielLoginResource


__author__ = 'viruzzz-kun'
__created__ = '08.02.2015'


boot = blinker.signal('coldstar.boot')
web_boot = blinker.signal('coldstar.lib.web.boot')
cas_boot = blinker.signal('coldstar.lib.castiel.boot')
self_boot = blinker.signal('coldstar.lib.castiel.web.boot')


@implementer(IResource)
class CastielWebResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.api = None
        self.login = None
        self.service = None
        self.putChild('', Data('I am Castiel, angel of God', 'text/html'))
        boot.connect(self.bootstrap_cas_web)
        cas_boot.connect(self.cas_boot)
        web_boot.connect(self.web_boot)

    def bootstrap_cas_web(self, root):
        print('Castiel Web: initialized')
        self_boot.send(self)

    def cas_boot(self, sender):
        """
        :type sender: coldstar.lib.castiel.service.CastielService
        :param sender:
        :return:
        """
        self.service = sender
        self.api = CastielApiResource(sender)
        self.login = CastielLoginResource(sender)
        self.putChild('api', self.api)
        self.putChild('login', self.login)
        print('Castiel Web: Castiel connected')

    def web_boot(self, sender):
        """
        :type sender: coldstar.lib.web.service.WebService
        :param sender:
        :return:
        """
        sender.root_resource.putChild('cas', self)
        print('Castiel Web: Main Web connected')


def make(config):
    web = CastielWebResource()
    return web