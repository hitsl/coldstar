# -*- coding: utf-8 -*-
from zope.interface import Interface

__author__ = 'viruzzz-kun'


class IWSService(Interface):
    def dispatch_message(self, message):
        """
        Internal dispatcher
        :param message:
        :return:
        """


class IPubSubService(Interface):
    def broadcast(self, uri, message):
        """
        Broadcast message
        """

    def subscribe(self, callback, uri):
        """
        Subscribe to uri
        :param uri: URI to subscribe
        :return:
        """

    def unsubscribe(self, callback, uri):
        """
        Unsubscribe
        :param callback: Callable
        :param uri: URI
        :return:
        """


class IRPCService(Interface):
    def register(self, callback, uri):
        """
        Register function to some URI
        :param callback: function
        :param uri: URI
        :return:
        """