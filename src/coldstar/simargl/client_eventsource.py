# -*- coding: utf-8 -*-
from coldstar.eventsource import make_event
from libsimargl.client import SimarglClient
from libcoldstar.plugin_helpers import Dependency
from twisted.internet.interfaces import ILoggingContext
from twisted.python import failure, log
from twisted.python.failure import Failure
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from zope.interface import implementer

__author__ = 'viruzzz-kun'


class Client(SimarglClient, Resource):
    isLeaf = 1
    cas = Dependency('coldstar.castiel')
    web = Dependency('libcoldstar.web')

    def __init__(self, config):
        SimarglClient.__init__(self, config)
        Resource.__init__(self)
        self.requests = set()

    def send(self, message):
        """
        :type message: libsimargl.message.Message
        :param message:
        :return:
        """
        if message.control:
            return
        event = make_event(message)
        for request in self.requests:
            if not (message.recipient and request.user != message.recipient):
                request.write(event)

    @web.on
    def web_boot(self, web):
        web.root_resource.putChild('simargl-es', self)

    def render(self, request):
        """
        :type request: libcoldstar.web.wrappers.TemplatedRequest
        :param request:
        :return:
        """
        if self.web.crossdomain(request, True):
            return ''
        if not self.cas:
            request.setResponseCode(500)
            return 'Cannot connect to CAS'

        def onFinish(result):
            log.msg("Connection from %s closed" % request.getClientIP(), system="Event Source")
            self.requests.remove(request)
            if not isinstance(result, Failure):
                return result

        def onUser(user_info):
            if isinstance(user_info, failure.Failure):
                request.setResponseCode(401, 'Authentication Failure')
                request.finish()
                return user_info
            else:
                request.user = user_info[0]
                request.setHeader('Content-Type', 'text/event-stream; charset=utf-8')
                request.write('')
                self.requests.add(request)
                request.notifyFinish().addBoth(onFinish)
                log.msg("Connection from %s established" % request.getClientIP(), system="Event Source")

        hex_token = request.getCookie('CastielAuthToken')
        if not hex_token:
            request.setResponseCode(401)
            return ''

        token = hex_token.decode('hex')

        self.cas.check_token(token).addBoth(onUser)
        return NOT_DONE_YET
