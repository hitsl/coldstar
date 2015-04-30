# -*- coding: utf-8 -*-
from coldstar.lib.eventsource import make_event
from coldstar.lib.gabriel.interfaces import IUserSession
from twisted.python.failure import Failure
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from zope.interface import implementer

__author__ = 'viruzzz-kun'


@implementer(IUserSession)
class GabrielEventSourceSession(object):
    def __init__(self, request):
        self.request = request

    def send(self, data):
        self.request.write(make_event(data))


class GabrielEventSourceResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.service = None
        self.web = None

    def render(self, request):
        """
        :type request: coldstar.lib.web.wrappers.TemplatedRequest
        :param request:
        :return:
        """
        request.setHeader('Content-Type', 'text/event-stream')

        user_id = request.get_auth()
        session = GabrielEventSourceSession(request)

        def on_finish(result):
            self.service.uninstall_session(user_id, session)
            if not isinstance(result, Failure):
                return result

        request.notifyFinish().addBoth(on_finish)
        self.service.install_session(user_id, session)
        request.write('')
        return NOT_DONE_YET