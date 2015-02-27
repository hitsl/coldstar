# -*- coding: utf-8 -*-
from zope.interface import Interface

__author__ = 'viruzzz-kun'


class IScanService(Interface):
    def getProducer(self, dev_name):
        """
        Get IProducer for dev_name
        :param dev_name: Scanner Device name
        :return:
        """

    def getScanners(self):
        """
        Get scanners
        :return:
        """