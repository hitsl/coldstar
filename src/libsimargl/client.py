# -*- coding: utf-8 -*-
from libcoldstar.plugin_helpers import ColdstarPlugin
from twisted.application.service import Service

__author__ = 'viruzzz-kun'


class SimarglClient(Service, ColdstarPlugin):
    def __init__(self, config):
        self.config = config

    def send(self, message):
        """
        :type message: coldstar.simargl.message.Message
        :param message:
        :return:
        """
        pass
