#!/usr/bin/env python
# -*- coding: utf-8 -*-
from libcoldstar.plugin_helpers import Dependency, ColdstarPlugin

from twisted.web.resource import IResource, Resource
from twisted.web.static import Data
from zope.interface import implementer
from .rpc import CastielApiResource
from .user_login import CastielLoginResource
from libcoldstar.web.wrappers import AutoRedirectResource

__author__ = 'viruzzz-kun'
__created__ = '08.02.2015'


@implementer(IResource)
class CastielWebResource(AutoRedirectResource, ColdstarPlugin):
    service = Dependency('coldstar.castiel')
    web = Dependency('libcoldstar.web')

    def __init__(self, config):
        Resource.__init__(self)
        self.config = config
        self.cookie_name = config.get('cookie_name', 'CastielAuthToken')
        self.cors_domain = config.get('cors_domain', '*')
        self.default_cookie_domain = config.get('cookie_domain', 'localhost')
        self.domain_map = config.get('domain_map', {})
        api_resource = CastielApiResource()
        api_resource.cors_domain = self.cors_domain
        self.putChild('api', api_resource)

        user_resource = CastielLoginResource()
        user_resource.cookie_name = self.cookie_name
        user_resource.get_cookie_domain = self.get_cookie_domain
        self.putChild('login', user_resource)
        self.service = None
        self.putChild('', Data('I am Castiel, angel of God', 'text/html'))

    def get_cookie_domain(self, source):
        return self.domain_map.get(source, self.default_cookie_domain)

    @web.on
    def web_boot(self, sender):
        """
        :type sender: libcoldstar.web.service.WebService
        :param sender:
        :return:
        """
        sender.root_resource.putChild('cas', self)


def make(config):
    web = CastielWebResource(config)
    return web