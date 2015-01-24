# -*- coding: utf-8 -*-
from twisted.python.components import registerAdapter
from coldstar.lib.db.interfaces import IDataBaseService
from coldstar.lib.utils import must_be_deferred
import os
import time
from hashlib import md5

from twisted.application.service import Service
from twisted.internet import defer
from twisted.internet.task import LoopingCall
from zope.interface import implementer

from .interfaces import ICasService
from coldstar.lib.excs import SerializableBaseException


__author__ = 'mmalkov'


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


@implementer(ICasService)
class CastielService(Service):
    expiry_time = 3600
    clean_period = 10
    check_duplicate_tokens = False

    def __init__(self, database_service):
        self.db = database_service
        self.tokens = {}
        self.expired_cleaner = None

    @defer.inlineCallbacks
    def acquire_token(self, login, password):
        from twisted.internet.threads import deferToThread
        from coldstar.application.castiel.models import Person

        def get_user_id():
            with self.db.context_session(True) as session:
                result = session.query(Person).filter(Person.login == login, Person.password == md5(password).hexdigest()).first()
                if result:
                    return result.id
                raise EInvalidCredentials

        user_id = yield deferToThread(get_user_id)

        ctime = time.time()
        if self.check_duplicate_tokens and any((age > ctime and user_id == uid) for token, (age, uid) in self.tokens.iteritems()):
            raise ETokenAlreadyAcquired(user_id)

        token = os.urandom(16)

        deadline = ctime + self.expiry_time
        self.tokens[token] = (deadline, user_id)
        defer.returnValue((token, deadline, user_id))

    @must_be_deferred
    def release_token(self, token):
        if token in self.tokens:
            del self.tokens[token]
            return defer.succeed(True)
        raise EExpiredToken(token)

    @must_be_deferred
    def check_token(self, token, prolong=False):
        if token not in self.tokens:
            raise EExpiredToken(token)
        deadline, user_id = self.tokens[token]
        if deadline < time.time():
            raise EExpiredToken(token)
        if prolong:
            self.prolong_token(token)
        return defer.succeed((user_id, deadline))

    @must_be_deferred
    def prolong_token(self, token):
        if token not in self.tokens:
            raise EExpiredToken(token)
        deadline = time.time() + self.expiry_time
        self.tokens[token] = (deadline, self.tokens[token][1])
        return defer.succeed((True, deadline))

    def _clean_expired(self):
        now = time.time()
        for token, (t, _) in self.tokens.items():
            if t < now:
                print "token", token.encode('hex'), "expired"
                del self.tokens[token]

    def startService(self):
        Service.startService(self)
        self.expired_cleaner = LoopingCall(self._clean_expired)
        self.expired_cleaner.start(self.clean_period)

    def stopService(self):
        Service.stopService(self)
        self.expired_cleaner.stop()

registerAdapter(CastielService, IDataBaseService, ICasService)