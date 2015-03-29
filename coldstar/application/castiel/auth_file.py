#!/usr/bin/env python
# -*- coding: utf-8 -*-
from hashlib import md5

from twisted.internet import defer
from twisted.python import failure

from zope.interface import implementer
from coldstar.lib.auth.exceptions import EInvalidCredentials
from coldstar.lib.auth.interfaces import IAuthenticator, IAuthObject


__author__ = 'viruzzz-kun'
__created__ = '08.02.2015'


@implementer(IAuthenticator)
class FileAuthenticator(object):
    def __init__(self, filename):
        self.filename = filename

    def get_user(self, login, password):
        d = defer.Deferred()
        if isinstance(password, unicode):
            pwd = password.encode('utf-8', errors='ignore')
        elif isinstance(password, str):
            pwd = password
        else:
            d.errback(failure.Failure(TypeError('password should be either unicode ot str')))
            return d
        userlist = {}
        with open(self.filename, 'rt') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    continue
                splits = line.split(':', 1)
                if len(splits) < 2:
                    continue
                userlist[splits[0]] = splits[1]
        if userlist.get(login, None) == pwd: #md5(pwd).hexdigest():
            d.callback(FileAuthObject(login))
        else:
            d.errback(failure.Failure(EInvalidCredentials()))
        return d


@implementer(IAuthObject)
class FileAuthObject(object):
    __slots__ = ['user_id', 'login']

    def __init__(self, login):
        self.user_id = login
        self.login = login
