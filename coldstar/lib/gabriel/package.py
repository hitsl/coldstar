# -*- coding: utf-8 -*-

__author__ = 'viruzzz-kun'


class Package(object):
    __slots__ = ['sender', 'recipient', 'uri', 'datetime', 'payload', 'magic', 'type']

    sender = None
    recipient = None
    uri = None
    datetime = None
    payload = None
    magic = None
    type = None

    def __json__(self):
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'uri': self.uri,
            'datetime': self.datetime,
            'payload': self.payload,
            'type': self.type,
            'magic': self.magic,
        }

    @classmethod
    def make_call(cls, uri, magic, *args, **kwargs):
        result = cls()
        result.type = 'call'
        result.magic = magic
        result.uri = uri
        result.payload = {
            'args': args,
            'kwargs': kwargs,
        }

    @classmethod
    def make_pm(cls, sender, recipient, text):
        result = cls()
        result.type = 'pm'
        result.sender = sender
        result.recipient = recipient
        result.payload = {
            'text': text,
        }

    @classmethod
    def make_bm(cls, sender, text):
        result = cls()
        result.type = 'bm'
        result.sender = sender
        result.payload = {
            'text': text,
        }
