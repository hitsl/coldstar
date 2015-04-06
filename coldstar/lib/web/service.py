#!/usr/bin/env python
# -*- coding: utf-8 -*-
import blinker

__author__ = 'viruzzz-kun'
__created__ = '04.04.2015'


cas_boot = blinker.signal('coldstar.lib.castiel.boot')
boot = blinker.signal('coldstar.boot')
self_boot = blinker.signal('coldstar.lib.web.boot')


class WebService(object):
    def __init__(self, config):
        import os
        from coldstar.lib.utils import safe_traverse

        from twisted.application.internet import TCPServer
        from coldstar.lib.web.wrappers import TemplatedSite, DefaultRootResource
        from coldstar.lib.proxied_logger import proxiedLogFormatter

        root_resource = DefaultRootResource()
        current_dir = os.path.dirname(__file__)
        site = TemplatedSite(
            root_resource,
            static_path=safe_traverse(config, 'static-path', default=os.path.join(current_dir, 'web', 'static')),
            template_path=safe_traverse(config, 'template-path', default=os.path.join(current_dir, 'web', 'templates')),
            logFormatter=proxiedLogFormatter)

        service = TCPServer(
            int(safe_traverse(config, 'port', default=5000)),
            site,
            interface=safe_traverse(config, 'host', default='127.0.0.1')
        )

        self.root_resource = root_resource
        self.site = site
        self.service = service
        self.cas = None

        boot.connect(self.bootstrap_web)
        cas_boot.connect(self.cas_boot)

    def bootstrap_web(self, parent):
        self.service.setServiceParent(parent)
        print('Web: initialized')
        self_boot.send(self)

    def cas_boot(self, sender):
        self.cas = sender
        print('Web: Cas connected')
