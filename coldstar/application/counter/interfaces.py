# -*- coding: utf-8 -*-
from zope.interface import Interface, Attribute

__author__ = 'viruzzz-kun'


class ICounterService(Interface):
    db = Attribute('db')

    def acquire(self, counter_id, client_id=None):
        """
        Acquire new external id
        :param counter_id: rbCounter.id
        :param client_id: Client.id
        :type counter_id: int
        :type client_id: int|None
        :return: new External Id
        :rtype: str
        """