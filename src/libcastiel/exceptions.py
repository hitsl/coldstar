#!/usr/bin/env python
# -*- coding: utf-8 -*-
from libcoldstar.excs import SerializableBaseException

__author__ = 'viruzzz-kun'
__created__ = '08.02.2015'


class EExpiredToken(SerializableBaseException):
    def __init__(self, token):
        self.token = token
        self.message = 'Token %s is expired or not taken' % token.encode('hex')


class ETokenAlreadyAcquired(SerializableBaseException):
    def __init__(self, user_id):
        self.message = 'Token for user id = %s already taken' % user_id


class EInvalidCredentials(SerializableBaseException):
    def __init__(self):
        self.message = 'Incorrect login or password'


class ENoToken(SerializableBaseException):
    def __init__(self):
        self.message = 'Token cookie is not set'

