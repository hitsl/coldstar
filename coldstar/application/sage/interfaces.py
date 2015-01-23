# -*- coding: utf-8 -*-
from zope.interface import Interface, Attribute

__author__ = 'viruzzz-kun'


class ISettingsService(Interface):
    db = Attribute('db', 'Database Service')

    def get_value(self, key, subtree):
        """
        Get value
        :param key: Key
        :param subtree: get all subtree
        :return:
        """

    def set_value(self, key, value):
        """
        Set value
        :param key: Key
        :param value: Value
        :return:
        """