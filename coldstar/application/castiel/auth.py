#!/usr/bin/env python
# -*- coding: utf-8 -*-
from hashlib import md5

from twisted.python.components import registerAdapter
from zope.interface import implementer
from coldstar.lib.db.interfaces import IDataBaseService
from .interfaces import IMisUserModel

from coldstar.lib.auth.exceptions import EInvalidCredentials
from coldstar.lib.auth.interfaces import IAuthenticator, IAuthObject


__author__ = 'viruzzz-kun'
__created__ = '08.02.2015'


@implementer(IAuthenticator)
class MisAuthenticator(object):
    def __init__(self, database):
        self.db = database

    def get_user(self, login, password):
        from twisted.internet.threads import deferToThread
        from coldstar.application.castiel.models import Person

        def get_user_w():
            with self.db.context_session(True) as session:
                if isinstance(password, unicode):
                    pwd = password.encode('utf-8', errors='ignore')
                elif isinstance(password, str):
                    pwd = password
                else:
                    raise TypeError('password should be either unicode ot str')
                result = session.query(Person).filter(
                    Person.login == login,
                    Person.password == md5(pwd).hexdigest()).first()

                if result:
                    return IAuthObject(result)
                raise EInvalidCredentials

        d = deferToThread(get_user_w)
        return d


@implementer(IAuthObject)
class MisAuthObject(object):
    __slots__ = ['user_id', 'login']

    def __init__(self, person):
        self.user_id = person.id
        self.login = person.login


registerAdapter(MisAuthObject, IMisUserModel, IAuthObject)
registerAdapter(MisAuthenticator, IDataBaseService, IAuthenticator)