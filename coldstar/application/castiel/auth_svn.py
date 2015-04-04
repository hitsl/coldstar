#!/usr/bin/env python
# -*- coding: utf-8 -*-
from hashlib import md5

from ConfigParser import ConfigParser, NoOptionError
from twisted.internet import defer
from twisted.python import failure

from zope.interface import implementer
from coldstar.lib.auth.exceptions import EInvalidCredentials
from coldstar.lib.auth.interfaces import IAuthenticator, IAuthObject


__author__ = 'viruzzz-kun'
__created__ = '08.02.2015'


@implementer(IAuthenticator)
class FileAuthenticator(object):
    def __init__(self, filename, authz=None):
        self.filename = filename
        self.authz = authz

    def get_user(self, login, password):
        if isinstance(password, unicode):
            pwd = password.encode('utf-8', errors='ignore')
        elif isinstance(password, str):
            pwd = password
        else:
            return defer.fail(failure.Failure(TypeError('password should be either unicode ot str')))
        with open(self.filename, 'rt') as f:
            cp = ConfigParser()
            cp.readfp(f)
        try:
            if cp.get('users', login, None) != pwd:
                raise KeyError
            obj = FileAuthObject(login)
            if self.authz:
                with open(self.authz, 'rt') as f:
                    authz = ConfigParser()
                    authz.readfp(f)
                for group_name, group_users in authz.items('groups'):
                    names = map(unicode.strip, group_users.split(','))
                    if login in names:
                        obj.groups.add(group_name)
            return defer.succeed(obj)
        except (KeyError, NoOptionError):
            pass
        return defer.fail(failure.Failure(EInvalidCredentials()))


@implementer(IAuthObject)
class FileAuthObject(object):
    __slots__ = ['user_id', 'login', 'groups']

    def __init__(self, login):
        self.user_id = login
        self.login = login
        self.groups = set()
