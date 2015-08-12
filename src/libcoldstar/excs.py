#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'viruzzz-kun'
__created__ = '15.10.2014'


class SerializableBaseException(Exception):
    def __json__(self):
        return {
            'success': False,
            'exception': self.__class__.__name__,
            'message': self.message,
        }

    def __unicode__(self):
        return u'<%s> "%s"' % (self.__class__.__name__, self.message)


class MethodNotFoundException(SerializableBaseException):
    def __init__(self, method_name):
        self.message = 'Method %s not found' % method_name


class LockNotFound(SerializableBaseException):
    def __init__(self, object_id):
        self.message = 'Lock not found for object "%s"' % object_id


class BadRequest(SerializableBaseException):
    def __init__(self):
        self.message = 'Bad Request'


class LockerNotSet(SerializableBaseException):
    def __init__(self):
        self.message = 'Locker not set'


class Unauthorized(SerializableBaseException):
    def __init__(self):
        self.message = 'Not Authorized'


class UnknownCommand(SerializableBaseException):
    def __init__(self, command):
        self.message = u'Unknown command %s' % command


class ExceptionWrapper(SerializableBaseException):
    def __init__(self, original_exception):
        self.o = original_exception

    def __json__(self):
        return {
            'exception': self.o.__class__.__name__,
            'message': unicode(self.o),
        }


