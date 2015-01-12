# -*- coding: utf-8 -*-
from twisted.python.components import registerAdapter
from twisted.web.server import Session
from zope.interface import Interface, implementer

__author__ = 'viruzzz-kun'


class IFlashedMessages(Interface):
    def get_flashed_messages(self):
        pass

    def flash_message(self, message):
        pass


@implementer(IFlashedMessages)
class FlashedMessages(object):
    def __init__(self, session):
        self.flashed_messages = []

    def get_flashed_messages(self):
        messages = self.flashed_messages
        self.flashed_messages = []
        return messages

    def flash_message(self, message):
        self.flashed_messages.append(message)


registerAdapter(FlashedMessages, Session, IFlashedMessages)