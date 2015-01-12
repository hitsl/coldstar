# -*- coding: utf-8 -*-
import os
import time

from twisted.application.service import Service
from twisted.internet import defer
from twisted.internet.task import LoopingCall
from hashlib import md5
from zope.interface import implementer

from application.castiel.interfaces import ICasService
from lib.excs import SerializableBaseException


__author__ = 'mmalkov'


class ERottenToken(SerializableBaseException):
    def __init__(self, token):
        self.token = token
        self.message = 'Token %s is expired' % token.encode('hex')


class ETokenAlreadyAcquired(SerializableBaseException):
    def __init__(self, user_id):
        self.message = 'Token for user id = %s already taken' % user_id


class EInvalidCredentials(SerializableBaseException):
    def __init__(self):
        self.message = 'Incorrect login or password'


@implementer(ICasService)
class CastielService(Service):
    rot_time = 3600
    clean_period = 10
    db_service = None
    check_duplicate_tokens = False

    def __init__(self):
        self.tokens = {}
        self.rot_cleaner = LoopingCall(self._clean_rotten)

    @defer.inlineCallbacks
    def acquire_token(self, login, password):
        from twisted.internet.threads import deferToThread
        from .models import Person

        def get_user_id():
            with self.db_service.context_session(True) as session:
                result = session.query(Person).filter(Person.login == login, Person.password == md5(password).hexdigest()).first()
                if result:
                    return result.id
                raise EInvalidCredentials

        user_id = yield deferToThread(get_user_id)

        ctime = time.time()
        if self.check_duplicate_tokens and any((age > ctime and user_id == uid) for token, (age, uid) in self.tokens.iteritems()):
            raise ETokenAlreadyAcquired(user_id)

        token = os.urandom(16)

        self.tokens[token] = (ctime + self.rot_time, user_id)
        defer.returnValue(token)

    def release_token(self, token):
        if token in self.tokens:
            del self.tokens[token]
            return True
        raise ERottenToken(token)

    def check_token(self, token, prolong=False):
        if token not in self.tokens:
            return False
        deadline, user_id = self.tokens[token]
        if deadline < time.time():
            return False
        if prolong:
            self.prolong_token(token)
        return user_id

    def prolong_token(self, token):
        if token not in self.tokens:
            raise ERottenToken(token)
        self.tokens[token] = (time.time() + self.rot_time, self.tokens[token][1])
        return True

    def _clean_rotten(self):
        now = time.time()
        for token, (t, _) in self.tokens.items():
            if t < now:
                del self.tokens[token]

    def startService(self):
        Service.startService(self)
        self.rot_cleaner.start(self.clean_period)

    def stopService(self):
        Service.stopService(self)
        self.rot_cleaner.stop()