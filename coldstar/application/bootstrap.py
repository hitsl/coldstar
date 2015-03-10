# -*- coding: utf-8 -*-
from ConfigParser import ConfigParser
import os

from twisted.web.resource import IResource
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
        from coldstar.lib.web.wrappers import TemplatedSite, DefaultRootResource
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

        self.root_resource = DefaultRootResource()
        current_dir = os.path.dirname(__file__)
        self.site = TemplatedSite(
            self.root_resource,
            os.path.join(current_dir, 'web', 'static'),
            os.path.join(current_dir, 'web', 'templates'),
            logFormatter=proxiedLogFormatter)

        self.web_service = TCPServer(
            int(safe_traverse(config, 'web', 'port', default=5000)),
            self.site,
            interface=safe_traverse(config, 'web', 'host', default='127.0.0.1')
        )
        self.web_service.setServiceParent(self)

        self.db_service = self.bootstrap_database(safe_traverse(config, 'database', default={}))
        self.castiel_service = self.bootstrap_castiel(safe_traverse(config, 'module', 'castiel', default={}))
        self.scan_service = self.bootstrap_scanner(safe_traverse(config, 'module', 'scan', default={}))

    def bootstrap_database(self, config):
        from coldstar.lib.db.service import DataBaseService

        service = DataBaseService(safe_traverse(config, 'url', default='mysql://tmis:q1w2e3r4t5@127.0.0.1/hospital1'))
        service.setServiceParent(self)

        return service

    def bootstrap_scanner(self, config):
        from coldstar.application.scanner.service import ScanService

        service = ScanService()
        service.cors_domain = safe_traverse(config, 'cors_domain', default='http://127.0.0.1:5000')
        service.setServiceParent(self)
        resource = IResource(service)
        self.root_resource.putChild('scan', resource)
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
        service.cors_domain = safe_traverse(config, 'cors_domain', default='http://127.0.0.1:5000')
        service.cookie_domain = safe_traverse(config, 'cookie_domain', default='127.0.0.1')
        service.setServiceParent(self)

        resource = IResource(service)
        self.root_resource.putChild('cas', resource)

        return service