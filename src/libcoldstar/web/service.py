#!/usr/bin/env python
# -*- coding: utf-8 -*-
from libcoldstar.plugin_helpers import ColdstarPlugin, Dependency
from twisted.application.service import MultiService

__author__ = 'viruzzz-kun'
__created__ = '04.04.2015'


class WebService(MultiService, ColdstarPlugin):
    signal_name = 'libcoldstar.web'
    cas = Dependency('libcoldstar.web')

    def __init__(self, config):
        MultiService.__init__(self)
        import os
        from libcoldstar.utils import safe_traverse

        from twisted.internet import reactor
        from twisted.application import strports
        from libcoldstar.web.wrappers import TemplatedSite, DefaultRootResource
        from libcoldstar.proxied_logger import proxiedLogFormatter

        root_resource = DefaultRootResource()
        current_dir = os.path.dirname(__file__)
        site = TemplatedSite(
            root_resource,
            static_path=safe_traverse(config, 'static-path', default=os.path.join(current_dir, 'web', 'static')),
            template_path=safe_traverse(config, 'template-path', default=os.path.join(current_dir, 'web', 'templates')),
            logFormatter=proxiedLogFormatter)

        description = config.get('strport', 'tcp:%s:interface=%s' % (
            config.get('port', 5000),
            config.get('host', '127.0.0.1')
        ))

        self.cors_domain = config.get('cors-domain', 'http://127.0.0.1:5000/')

        service = strports.service(description, site, reactor=reactor)
        service.setServiceParent(self)

        self.root_resource = root_resource
        self.site = site
        self.service = service

    def crossdomain(self, request, allow_credentials=False):
        request.setHeader('Access-Control-Allow-Origin', self.cors_domain)
        if allow_credentials:
            request.setHeader('Access-Control-Allow-Credentials', 'true')
        if request.method == 'OPTIONS' and request.requestHeaders.hasHeader('Access-Control-Request-Method'):
            # Preflight Request
            request.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            request.setHeader('Access-Control-Allow-Headers', 'Content-Type')
            request.setHeader('Access-Control-Max-Age', '600')
            return True
