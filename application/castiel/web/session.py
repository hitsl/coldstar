# -*- coding: utf-8 -*-
from twisted.python.components import registerAdapter
from twisted.web.server import Session
from zope.interface import Interface, Attribute, implementer

__author__ = 'viruzzz-kun'


class ICastielWebSession(Interface):
    flashed_messages = Attribute('Flashed Messages')
    back = Attribute('Where to return after login success')

    def get_flashed_messages(self):
        pass

    def flash_message(self, message):
        pass


@implementer(ICastielWebSession)
class CastielWebSession(object):
    def __init__(self, session):
        self.flashed_messages = []
        self.back = None

    def get_flashed_messages(self):
        messages = self.flashed_messages
        self.flashed_messages = []
        return messages

    def flash_message(self, message):
        self.flashed_messages.append(message)


registerAdapter(CastielWebSession, Session, ICastielWebSession)