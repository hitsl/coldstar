# -*- coding: utf-8 -*-
import twisted.web.resource
import twisted.web.static
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
        self.root_resource.putChild('', twisted.web.static.Data(u"""
<!DOCTYPE html>
<html>
<head><style>body {background: #5090F0; color: white}</style></head>
<body><h1>ColdStar</h1><h2>Подсистема всякой ерунды</h2>Давайте придумаем более человеческое название...</body>
</html>""".encode('utf-8'), 'text/html; charset=utf-8'))
        self.site = Site(self.root_resource)

        self.web_service = internet.TCPServer(
            int(config.get('port', 5000)),
            self.site,
            interface=config.get('interface', '0.0.0.0')
        )
        self.web_service.setServiceParent(self)

        self.db_service = self.bootstrap_database(config)
        self.coldstar_service = self.bootstrap_coldstar(config)
        self.castiel_service = self.bootstrap_castiel(config)

    def bootstrap_database(self, config):
        from application.db.service import DataBaseService

        service = DataBaseService(config.get('db-url', 'mysql+cymysql://tmis:q1w2e3r4t5@127.0.0.1/hospital1'))
        service.setServiceParent(self)

        return service

    def bootstrap_coldstar(self, config):
        from autobahn.twisted.resource import WebSocketResource
        from twisted.web.resource import IResource
        from application.coldstar.interfaces import IWsLockFactory

        from application.coldstar.service import ColdStarService
        from application.coldstar.test_page import TestPageResource

        service = ColdStarService()
        service.short_timeout = int(config.get('tmp-lock-timeout', 60))
        service.long_timeout = int(config.get('lock-timeout', 3600))
        service.setServiceParent(self)

        rest_resource = IResource(service)

        ws_factory = IWsLockFactory(service)
        ws_resource = WebSocketResource(ws_factory)

        test_page_resource = TestPageResource()

        self.root_resource.putChild('lock', rest_resource)
        self.root_resource.putChild('ws', ws_resource)
        self.root_resource.putChild('test', test_page_resource)

        return service

    def bootstrap_castiel(self, config):
        from twisted.web.resource import IResource
        from application.castiel.service import CastielService

        service = CastielService()
        service.db_service = self.db_service
        service.setServiceParent(self)

        resource = IResource(service)
        self.root_resource.putChild('cas', resource)

        return service