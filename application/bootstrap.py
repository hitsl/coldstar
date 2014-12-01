# -*- coding: utf-8 -*-
import twisted.web.resource
import twisted.application.service

__author__ = 'mmalkov'


class RootService(twisted.application.service.MultiService):
    def __init__(self, config):
        twisted.application.service.MultiService.__init__(self)
        from twisted.application import internet
        from twisted.web.resource import Resource
        from twisted.web.server import Site

        # noinspection PyUnresolvedReferences

        self.root_resource = twisted.web.resource.Resource()
        self.site = Site(self.root_resource)

        self.web_service = internet.TCPServer(
            int(config.get('port', 5000)),
            self.site,
            interface=config.get('interface', '0.0.0.0')
        )
        self.web_service.setServiceParent(self)

        self.bootstrap_coldstar(config)
        self.bootstrap_castiel(config)

    def bootstrap_coldstar(self, config):
        from autobahn.twisted.resource import WebSocketResource
        from twisted.web.resource import IResource
        from application.coldstar.interfaces import IWsLockFactory

        from application.coldstar.service import ColdStarService
        from application.coldstar.test_page import TestPageResource

        cold_star = ColdStarService()
        cold_star.short_timeout = int(config.get('tmp-lock-timeout', 60))
        cold_star.long_timeout = int(config.get('lock-timeout', 3600))
        cold_star.setServiceParent(self)

        rest_resource = IResource(cold_star)

        ws_factory = IWsLockFactory(cold_star)
        ws_resource = WebSocketResource(ws_factory)

        test_page_resource = TestPageResource()

        self.root_resource.putChild('lock', rest_resource)
        self.root_resource.putChild('ws', ws_resource)
        self.root_resource.putChild('test', test_page_resource)

    def bootstrap_castiel(self, config):
        from twisted.web.resource import IResource
        from application.castiel.service import CastielService

        service = CastielService()
        service.setServiceParent(self)

        resource = IResource(service)
        self.root_resource.putChild('cas', resource)