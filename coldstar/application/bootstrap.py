# -*- coding: utf-8 -*-
import yaml
import twisted.web.static

from twisted.web.resource import IResource, Resource
from twisted.application.service import MultiService

from coldstar.lib.utils import safe_traverse


__author__ = 'mmalkov'


class RootService(MultiService):
    def __init__(self, arg_config):
        MultiService.__init__(self)
        from twisted.application.internet import TCPServer
        from twisted.web.server import Site

        config = {}

        try:
            with open('config_dist.yaml') as cfg_file:
                config.update(yaml.load(cfg_file))
        except (IOError, OSError):
            pass

        try:
            with open(arg_config['config'], 'rt') as cfg_file:
                config.update(yaml.load(cfg_file))
        except (IOError, OSError):
            print(u'Cannot load config. Using defaults.')

        self.root_resource = Resource()
        self.root_resource.putChild('', twisted.web.static.Data(u"""
<!DOCTYPE html>
<html>
<head><style>body {background: #5090F0; color: white}</style></head>
<body><h1>ColdStar</h1><h2>Подсистема всякой ерунды</h2>Давайте придумаем более человеческое название...</body>
</html>""".encode('utf-8'), 'text/html; charset=utf-8'))
        self.site = Site(self.root_resource)

        self.web_service = TCPServer(
            int(safe_traverse(config, 'web', 'port', default=5000)),
            self.site,
            interface=safe_traverse(config, 'host', default='127.0.0.1')
        )
        self.web_service.setServiceParent(self)

        self.db_service = self.bootstrap_database(safe_traverse(config, 'database', default={}))
        self.cerber_service = self.bootstrap_cerber(safe_traverse(config, 'modules', 'cerber', default={}))
        self.castiel_service = self.bootstrap_castiel(safe_traverse(config, 'modules', 'castiel', default={}))
        self.sage_service = self.bootstrap_sage(safe_traverse(config, 'modules', 'sage', default={}))
        self.counter_service = self.bootstrap_counter(safe_traverse(config, 'modules', 'counter', default={}))

    def bootstrap_database(self, config):
        from coldstar.lib.db.service import DataBaseService

        service = DataBaseService(safe_traverse(config, 'url', default='mysql://tmis:q1w2e3r4t5@127.0.0.1/hospital1'))
        service.setServiceParent(self)

        return service

    def bootstrap_sage(self, config):
        from coldstar.application.sage.interfaces import ISettingsService

        service = ISettingsService(self.db_service)
        self.setServiceParent(self)

        resource = IResource(service)
        self.root_resource.putChild('sage', resource)

        return service

    def bootstrap_counter(self, config):
        from coldstar.application.counter.interfaces import ICounterService

        service = ICounterService(self.db_service)
        service.setServiceParent(self)

        resource = IResource(service)
        self.root_resource.putChild('counter', resource)

        return service

    def bootstrap_cerber(self, config):
        from autobahn.twisted.resource import WebSocketResource
        from coldstar.application.cerber.interfaces import IWsLockFactory

        from coldstar.application.cerber.service import ColdStarService
        from coldstar.application.cerber.test_page import TestPageResource

        service = ColdStarService()
        service.short_timeout = int(safe_traverse(config, 'rest_expiry_time', default=60))
        service.long_timeout = int(safe_traverse(config, 'expiry_time', default=3600))
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
        from coldstar.application.castiel.interfaces import ICasService

        service = ICasService(self.db_service)
        service.expiry_time = int(safe_traverse(config, 'expiry_time', default=3600))
        service.clean_period = int(safe_traverse(config, 'clean_period', default=10))
        service.check_duplicate_tokens = safe_traverse(config, 'check_duplicate_tokens', default=False)
        service.setServiceParent(self)

        resource = IResource(service)
        self.root_resource.putChild('cas', resource)

        return service