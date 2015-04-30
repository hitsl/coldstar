# -*- coding: utf-8 -*-
from zope.interface import Interface, Attribute

__author__ = 'viruzzz-kun'


class IUserNotifications(Interface):
    id = Attribute('id')
    user_id = Attribute('user_id')
    datetime = Attribute('datetime')
    read = Attribute('read')
    data = Attribute('data')


class IUserSession(Interface):
    def send(self, data):
        """
        Send data to client
        :param data:
        :return:
        """