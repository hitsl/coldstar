# -*- coding: utf-8 -*-
from coldstar.lib.excs import SerializableBaseException

__author__ = 'viruzzz-kun'


class NoSuchMethod(SerializableBaseException):
    def __init__(self, uri):
        self.message = u'No such method: %s' % uri


class MethodAlreadyRegistered(SerializableBaseException):
    def __init__(self, uri):
        self.message = u'Method already registered: %s' % uri


class MethodUriMismatch(SerializableBaseException):
    def __init__(self, uri):
        self.message = u'Tried unregistering method from uri "%s", however this method wasn\'t registered' % uri