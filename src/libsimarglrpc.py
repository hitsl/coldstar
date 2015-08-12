# -*- coding: utf-8 -*-
from libcoldstar.api_helpers import get_json
from libcoldstar.plugin_helpers import ColdstarPlugin
from libsimargl.message import Message

__author__ = 'viruzzz-kun'


class Notifications(ColdstarPlugin):
    signal_name = 'coldstar.simargl'

    def __init__(self, config):
        self.api_url = config.get('url', 'http://127.0.0.1:5002/').rstrip('/') + '/simargl-rpc/'

    def inject_message(self, message):
        """
        Здесь должен происходить некоторый роутинг
        :type message: coldstar.simargl.message.Message
        :param message:
        :return:
        """
        get_json(self.api_url, json=message)


def make(config):
    return Notifications(config)
