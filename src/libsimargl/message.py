# -*- coding: utf-8 -*-
from libcoldstar.utils import as_json

__author__ = 'viruzzz-kun'


class Message(object):
    immediate = True   # Мгновенное сообщение: будет ставиться в очередь, не пишется в лог
    secondary = False  # Вторичное сообщение: не пишется в лог
    control = False    # Управляющее сообщение: для управления клиентами
    magic = None       # Магическое число для RPC
    topic = None       # тема сообщения
    sender = None      # User ID отправителя
    recipient = None   # User ID получателя
    envelope = False   # Пачка

    def __init__(self):
        self.tags = set()
        self.hops = []
        self.data = None

    def make_magic(self):
        import os
        self.magic = os.urandom(16)

    def __json__(self):
        return {
            'i': bool(self.immediate),
            's': bool(self.secondary),
            'envelope': bool(self.envelope),
            'ctrl': self.control,
            'topic': self.topic,
            'magic': self.magic,
            'sender': self.sender,
            'recipient': self.recipient,
            'tags': sorted(self.tags),
            'data': self.data,
            'hops': self.hops,
        }

    @classmethod
    def from_json(cls, j):
        result = cls()
        result.merge_with_dict(j)
        return result

    def merge_with_dict(self, j):
        self.control = j.get('ctrl', False)
        self.magic = j.get('magic', None)
        self.topic = j.get('topic', None)
        self.sender = j.get('sender')
        self.recipient = j.get('recipient')
        self.tags = set(j.get('tags', []))
        self.data = j.get('data')
        self.immediate = j.get('i', True)
        self.secondary = j.get('s', False)
        self.envelope = j.get('envelope', False)
        self.hops = j.get('hops', [])
