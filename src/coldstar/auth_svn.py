#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ConfigParser import ConfigParser, NoOptionError

from libcoldstar.plugin_helpers import ColdstarPlugin
from twisted.internet import defer
from twisted.python import failure
from zope.interface import implementer
from libcastiel.exceptions import EInvalidCredentials
from libcastiel.interfaces import IAuthenticator, IAuthObject

__author__ = 'viruzzz-kun'
__created__ = '08.02.2015'


@implementer(IAuthObject)
class SvnAuthObject(object):
    __slots__ = ['user_id', 'login', 'groups']
    msgpack = 1

    def __init__(self, login=None):
        self.user_id = login
        self.login = login
        self.groups = []

    def __getstate__(self):
        return [
            self.user_id,
            self.login,
            self.groups,
        ]

    def __setstate__(self, state):
        self.user_id, self.login, self.groups = state

@implementer(IAuthenticator)
class SvnAuthenticator(ColdstarPlugin):
    signal_name = 'libcoldstar.auth'

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
            obj = SvnAuthObject(login)
            if self.authz:
                with open(self.authz, 'rt') as f:
                    authz = ConfigParser()
                    authz.readfp(f)
                for group_name, group_users in authz.items('groups'):
                    names = [u.strip() for u in group_users.split(',')]
                    if login in names:
                        obj.groups.append(group_name)
                obj.groups = list(set(obj.groups))
            return defer.succeed(obj)
        except (KeyError, NoOptionError):
            pass
        return defer.fail(failure.Failure(EInvalidCredentials()))


def make(config):
    return SvnAuthenticator(config['passwd'], config.get('authz', None))