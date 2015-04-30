# -*- coding: utf-8 -*-
from coldstar.lib.eventsource import make_event
from coldstar.lib.gabriel.interfaces import IGabrielSession, IWebSocketProtocol
from twisted.python.components import registerAdapter
from twisted.web.iweb import IRequest
from zope.interface import implementer


__author__ = 'viruzzz-kun'


class SessionRegisterMixin:
    session_manager = None
    user_id = None

    def register(self):
        self.session_manager.register_session(self.user_id, self)

    def unregister(self):
        self.session_manager.unregister_session(self.user_id, self)


class SessionSubscriptionMixin:
    def __init__(self):
        self.subscriptions = {}

    def subscribe(self, uri):
        self.subscriptions[uri] = 1

    def unsubscribe(self, uri):
        self.subscriptions.pop(uri)



@implementer(IGabrielSession)
class RequestGabrielSession(object, SessionRegisterMixin, SessionSubscriptionMixin):
    session_manager = None
    user_id = None

    def __init__(self, request):
        """
        :type request: coldstar.lib.web.wrappers.TemplatedRequest
        :param request:
        :return:
        """
        SessionSubscriptionMixin.__init__(self)
        self.request = request

    def received_call(self, uri, *args, **kwargs):
        if self.session_manager:
            return self.session_manager.call(uri, *args, **kwargs)

    def received_broadcast(self, uri, data):
        if self.session_manager:
            self.session_manager.broadcast(uri, data)

    def system_broadcast(self, uri, data):
        if uri in self.subscriptions:
            self.request.write(make_event(data, uri))


@implementer(IGabrielSession)
class WebSocketGabrielSession(object, SessionRegisterMixin):
    session_manager = None
    user_id = None

    def __init__(self, protocol):
        """
        :type protocol: coldstar.lib.gabriel.ws.WsProtocol
        :param protocol:
        :return:
        """
        self.protocol = protocol

    def received_call(self, uri, *args, **kwargs):
        if self.session_manager:
            return self.session_manager.call(uri, *args, **kwargs)

    def received_broadcast(self, uri, data):
        if self.session_manager:
            self.session_manager.broadcast(uri, data)

    def system_broadcast(self, uri, data):
        if uri in self.subscriptions:
            self.protocol.sendNotification(uri, data)


registerAdapter(RequestGabrielSession, IRequest, IGabrielSession)
registerAdapter(WebSocketGabrielSession, IWebSocketProtocol, IGabrielSession)

