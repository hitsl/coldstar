# -*- coding: utf-8 -*-
from libcoldstar.api_helpers import get_json
from libcoldstar.plugin_helpers import ColdstarPlugin
from libsimargl.message import Message

__author__ = 'viruzzz-kun'


class Notifications(ColdstarPlugin):
    signal_name = 'libsimarglrpc'

    def __init__(self, config):
        self.api_url = config.get('url', 'http://127.0.0.1:5002/').rstrip('/') + '/simargl-rpc/'

    def notify_ezekiel_lock_released(self, object_id):
        message = Message()
        message.topic = 'ezekiel.lock.release'
        message.data = {
            'object_id': object_id
        }
        return get_json(self.api_url, json=message)


def make(config):
    return Notifications(config)
