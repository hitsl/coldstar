# -*- coding: utf-8 -*-
import json

import blinker
from libcoldstar.utils import api_method, as_json
from libsimargl.client import SimarglClient
from libsimargl.message import Message
from libcoldstar.plugin_helpers import Dependency
from twisted.internet import defer
from twisted.web.resource import Resource
from libcoldstar.msgpack_helpers import load

__author__ = 'viruzzz-kun'


class Client(SimarglClient, Resource):
    isLeaf = 1
    simargl_client = None
    web = Dependency('libcoldstar.web')
    cas = Dependency('coldstar.castiel')

    @web.on
    def on_boot(self, web):
        web.root_resource.putChild('simargl-rpc', self)

    def render(self, request):
        """
        :type request: libcoldstar.web.wrappers.TemplatedRequest
        :param request:
        :return:
        """
        if self.web.crossdomain(request, allow_credentials=True):
            return ''
        main, sub = request.get_content_type()
        if not main:
            main, sub = 'application', 'json'
        content = request.content.getvalue()
        if sub in ('msgpack', 'application/x-msgpack'):
            data = load(content)
        elif sub == 'json':
            data = json.loads(content, 'utf-8')
        else:
            request.setResponseCode(400, 'Unknown Content Type')
            defer.returnValue('')

        message = Message.from_json(data)

        from twisted.internet import reactor
        reactor.callLater(0, self.parent.dispatch_message, self, message=message)

        request.setHeader('content-type', 'application/json; charset=utf-8')
        return as_json({
            'success': True
        })

    def getUser(self, request, required=False):
        user = request.getUser()
        if user:
            return defer.succeed(user)
        token = request.getCookie('CastielAuthToken')
        if token:
            def _cb(user_info):
                request.user = user_info[0]
                return user_info[0]

            def _eb(f):
                if required:
                    f.printTraceback()
                    request.setResponseCode(401, 'Token expired or not valid')
                    return f

            return self.cas.check_token(token).addCallbacks(_cb, _eb)
        if required:
            return defer.fail()
        return defer.succeed(None)
