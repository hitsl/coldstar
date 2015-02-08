# -*- coding: utf-8 -*-
from ConfigParser import ConfigParser
import twisted.web.static

from twisted.web.resource import IResource, Resource
from twisted.application.service import MultiService

from coldstar.lib.utils import safe_traverse, safe_int


__author__ = 'mmalkov'


def parse_config(fp):
    cp = ConfigParser()
    cp.readfp(fp)
    result = {}
    for section in cp.sections():
        if ':' in section:
            upper, lower = section.split(':', 1)
            tmp = result[upper] = {}
            tmp[lower] = dict((k, safe_int(v)) for k, v in cp.items(section))
        else:
            result[section] = dict((k, safe_int(v)) for k, v in cp.items(section))
    return result


class RootService(MultiService):
    def __init__(self, arg_config):
        MultiService.__init__(self)
        from twisted.application.internet import TCPServer
        from twisted.web.server import Site
        from coldstar.lib.proxied_logger import proxiedLogFormatter

        config = {}

        try:
            with open('default.conf') as cfg_file:
                config.update(parse_config(cfg_file))
        except (IOError, OSError):
            pass

        if arg_config['config']:
            try:
                with open(arg_config['config'], 'rt') as cfg_file:
                    config.update(parse_config(cfg_file))
            except (IOError, OSError):
                print(u'Cannot load config. Using defaults.')

        self.root_resource = Resource()
        self.root_resource.putChild('', twisted.web.static.Data(u"""
<!DOCTYPE html>
<html>
<head><style>body {background: #5090F0; color: white}</style></head>
<body><h1>ColdStar</h1><h2>Подсистема всякой ерунды</h2>Давайте придумаем более человеческое название...</body>
</html>""".encode('utf-8'), 'text/html; charset=utf-8'))
        self.site = Site(self.root_resource, logFormatter=proxiedLogFormatter)

        self.web_service = TCPServer(
            int(safe_traverse(config, 'web', 'port', default=5000)),
            self.site,
            interface=safe_traverse(config, 'web', 'host', default='127.0.0.1')
        )
        self.web_service.setServiceParent(self)

        self.db_service = self.bootstrap_database(safe_traverse(config, 'database', default={}))
        # self.cerber_service = self.bootstrap_cerber(safe_traverse(config, 'module', 'cerber', default={}))
        self.castiel_service = self.bootstrap_castiel(safe_traverse(config, 'module', 'castiel', default={}))
        self.sage_service = self.bootstrap_sage(safe_traverse(config, 'module', 'sage', default={}))
        self.counter_service = self.bootstrap_counter(safe_traverse(config, 'module', 'counter', default={}))

    def bootstrap_database(self, config):
        from coldstar.lib.db.service import DataBaseService

        service = DataBaseService(safe_traverse(config, 'url', default='mysql://tmis:q1w2e3r4t5@127.0.0.1/hospital1'))
        service.setServiceParent(self)

        return service

    def bootstrap_sage(self, config):
        from coldstar.application.sage.interfaces import ISettingsService

        service = ISettingsService(self.db_service)
        service.setServiceParent(self)

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
        from coldstar.application.castiel import auth
        from coldstar.lib.castiel.interfaces import ICasService
        from coldstar.lib.auth.interfaces import IAuthenticator

        auth = IAuthenticator(self.db_service)
        service = ICasService(auth)
        service.expiry_time = int(safe_traverse(config, 'expiry_time', default=3600))
        service.clean_period = int(safe_traverse(config, 'clean_period', default=10))
        service.check_duplicate_tokens = safe_traverse(config, 'check_duplicate_tokens', default=False)
        service.setServiceParent(self)

        resource = IResource(service)
        self.root_resource.putChild('cas', resource)

        return service