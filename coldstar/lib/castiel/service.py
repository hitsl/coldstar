# -*- coding: utf-8 -*-
import os
import time

from twisted.python import failure
from twisted.python.components import registerAdapter
from twisted.application.service import Service
from twisted.internet import defer
from twisted.internet.task import LoopingCall
from zope.interface import implementer

from coldstar.lib.auth.interfaces import IAuthenticator
from .exceptions import EExpiredToken, ETokenAlreadyAcquired
from .interfaces import ICasService


__author__ = 'mmalkov'


@implementer(ICasService)
class CastielService(Service):
    expiry_time = 3600
    clean_period = 10
    check_duplicate_tokens = False

    def __init__(self, auth):
        self.auth = auth
        self.tokens = {}
        self.expired_cleaner = None

    def acquire_token(self, login, password):
        def _cb(user):
            user_id = user.user_id
            ctime = time.time()
            if self.check_duplicate_tokens and any((age > ctime and user_id == uid) for token, (age, uid) in self.tokens.iteritems()):
                return failure.Failure(ETokenAlreadyAcquired(user_id))

            token = os.urandom(16)

            deadline = ctime + self.expiry_time
            self.tokens[token] = (deadline, user_id)
            return token, deadline, user_id

        d = self.auth.get_user(login, password)
        d.addCallback(_cb)
        return d

    def release_token(self, token):
        if token in self.tokens:
            del self.tokens[token]
            return defer.succeed(True)
        return failure.Failure(EExpiredToken(token))

    def check_token(self, token, prolong=False):
        if token not in self.tokens:
            return failure.Failure(EExpiredToken(token))
        deadline, user_id = self.tokens[token]
        if deadline < time.time():
            return failure.Failure(EExpiredToken(token))
        if prolong:
            self.prolong_token(token)
        return defer.succeed((user_id, deadline))

    def prolong_token(self, token):
        if token not in self.tokens:
            return failure.Failure(EExpiredToken(token))
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

registerAdapter(CastielService, IAuthenticator, ICasService)