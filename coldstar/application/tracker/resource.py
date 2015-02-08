#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from twisted.web import resource
from twisted.python.components import registerAdapter
from .bencode import encode
from .exceptions import TorrentRegistryException
from .interfaces import ITorrentRegistry

__author__ = 'viruzzz-kun'
__created__ = '07.02.2015'


log = logging.getLogger('com.tracker')
log.setLevel(logging.DEBUG)


class TrackerResource(resource.Resource):
    INTERVAL = 300

    def __init__(self, registry):
        resource.Resource.__init__(self)
        self.registry = registry

    def render_GET(self, request):
        """
        Render GET
        :type request: twisted.web.server.Request
        :return:
        """
        try:
            ip = request.requestHeaders.getRawHeaders(b"x-forwarded-for", [request.getClientIP()])[0].split(b",")[0].strip()
            info_hash = request.args['info_hash'][0]
            compact = request.args['compact'][0].lower() not in ('0', 'false')
            port = int(request.args['port'][0])
            peer_id = request.args['peer_id'][0]

            event = request.args.get('event', [''])[0]
            # TODO: process 'started', 'completed' and 'stopped' events
            if event == 'stopped':
                self.registry.remove_peer(info_hash, peer_id, ip, port)
            else:
                self.registry.add_peer(info_hash, peer_id, ip, port)
            return encode({
                "interval": self.INTERVAL,
                "complete": 0,
                "incomplete": 0,
                "peers": self.registry.peer_list(info_hash, compact)
            })
        except TorrentRegistryException, e:
            log.error(e.message)
            return encode({
                'failure reason': str(e)
            })
        except Exception, e:
            import traceback, sys

            traceback.print_exc()
            return encode({
                'failure reason': (u'Internal server error: %s' % unicode(e)).encode('utf-8'),
                # 'traceback': traceback.extract_tb(traceback.extract_stack())
            })


registerAdapter(TrackerResource, ITorrentRegistry, resource.IResource)