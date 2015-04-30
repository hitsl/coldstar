# -*- coding: utf-8 -*-
from zope.interface import Interface, Attribute

__author__ = 'viruzzz-kun'


class IUserSession(Interface):
    def notify_user(self, message):
        """
        Method to send notification to user
        :type message: IMessage
        :param message:
        :return:
        """

    def send_data(self, uri, data):
        """
        Method to send data to user application
        :type uri: str
        :type data: dict
        :param uri: URI
        :param data:
        :return:
        """


class IAppSession(Interface):
    def send_data(self, uri, data):
        """
        Method to send data to application
        :type uri: str
        :type data: dict
        :param uri: URI
        :param data:
        :return:
        """


class IGabrielSession(Interface):
    """
    Gabriel Session
    """

    session_manager = Attribute('session_manager')
    user_id = Attribute('user_id')

    def register(self):
        pass

    def unregister(self):
        pass

    def subscribe(self, uri):
        pass

    def unsubscribe(self, uri):
        pass

    def received_call(self, uri, *args, **kwargs):
        pass

    def received_broadcast(self, uri, data):
        pass

    def system_broadcast(self, uri, data):
        pass


class IWebSocketProtocol(Interface):
    """
    WebSocket Protocol
    """


class IUserNotifications(Interface):
    id = Attribute('id')
    user_id = Attribute('user_id')
    datetime = Attribute('datetime')
    read = Attribute('read')
    data = Attribute('data')


