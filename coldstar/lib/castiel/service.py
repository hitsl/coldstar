# -*- coding: utf-8 -*-
import os
import time

import msgpack
import blinker

from twisted.python import failure, components
from twisted.python.components import registerAdapter
from twisted.application.service import Service
from twisted.internet import defer
from twisted.internet.task import LoopingCall
from zope.interface import implementer

from coldstar.lib.auth.interfaces import IAuthenticator
from .exceptions import EExpiredToken, ETokenAlreadyAcquired
from .interfaces import ICasService, IAuthTokenObject


__author__ = 'mmalkov'


@implementer(IAuthTokenObject)
class AuthTokenObject(object):
    __slots__ = ['token', 'deadline', 'user_id']

    def __init__(self, user_id, deadline, token=None):
        self.user_id = user_id
        self.token = os.urandom(16) if token is None else token
        self.deadline = deadline


class CastielUserRegistry(dict, components.Componentized):
    pass


@implementer(ICasService)
class CastielService(Service):
    expiry_time = 3600
    clean_period = 10
    check_duplicate_tokens = False
    cors_domain = 'http://127.0.0.1:5000'
    cookie_domain = '127.0.0.1'

    def __init__(self, auth):
        self.auth = auth
        self.tokens = CastielUserRegistry()
        self.expired_cleaner = None

    def acquire_token(self, login, password):
        def _cb(user):
            user_id = user.user_id
            ctime = time.time()
            if self.check_duplicate_tokens and any(
                    (ato.deadline > ctime and user_id == ato.user_id)
                    for token, ato in self.tokens.iteritems()
            ):
                return failure.Failure(ETokenAlreadyAcquired(user_id))

            token = os.urandom(16)

            deadline = ctime + self.expiry_time
            ato = self.tokens[token] = AuthTokenObject(user_id, deadline, token)  # (deadline, user_id)
            blinker.signal('coldstar.castiel.token.acquired').send(self, token=token, ato=ato)
            return ato

        def _eb(f):
            blinker.signal('coldstar.castiel.token.invalid_credentials').send(self, login=login, password=password)
            return f

        d = self.auth.get_user(login, password)
        d.addCallbacks(_cb, _eb)
        return d

    def release_token(self, token):
        if token in self.tokens:
            ato = self.tokens[token]
            blinker.signal('coldstar.castiel.token.expired').send(self, token=token, ato=ato)
            blinker.signal('coldstar.castiel.token.released').send(self, token=token, ato=ato)
            del self.tokens[token]
            return defer.succeed(True)
        return failure.Failure(EExpiredToken(token))

    def check_token(self, token, prolong=False):
        if token not in self.tokens:
            return failure.Failure(EExpiredToken(token))
        ato = self.tokens[token]
        if ato.deadline < time.time():
            return failure.Failure(EExpiredToken(token))
        if prolong:
            self.prolong_token(token)
        return defer.succeed((ato.user_id, ato.deadline))

    def prolong_token(self, token):
        if token not in self.tokens:
            return failure.Failure(EExpiredToken(token))
        deadline = time.time() + self.expiry_time
        ato = self.tokens[token]
        ato.deadline = deadline
        return defer.succeed((True, deadline))

    def is_valid_credentials(self, login, password):
        return self.auth.get_user(login, password)

    def _clean_expired(self):
        now = time.time()
        for token, ato in self.tokens.items():
            if ato.deadline < now:
                print "token", token.encode('hex'), "expired"
                blinker.signal('coldstar.castiel.token.expired').send(self, token=token, ato=ato)
                del self.tokens[token]

    def get_user_quick(self, token):
        if token not in self.tokens:
            return None
        ato = self.tokens[token]
        if ato.deadline < time.time():
            return None
        return ato

    def startService(self):
        try:
            with open('tokens.msgpack', 'rb') as f:
                self.tokens = dict(
                    (i[2], AuthTokenObject(i[0], i[1], i[2]))
                    for i in msgpack.unpack(f)
                )
        except (IOError, OSError, msgpack.UnpackException, msgpack.UnpackValueError):
            pass
        self.expired_cleaner = LoopingCall(self._clean_expired)
        self.expired_cleaner.start(self.clean_period)
        Service.startService(self)
        blinker.signal('coldstar.castiel.service.started').send(self)

    def stopService(self):
        self.expired_cleaner.stop()
        with open('tokens.msgpack', 'wb') as f:
            msgpack.pack([
                [obj.user_id, obj.deadline, token]
                for token, obj in self.tokens.iteritems()
            ], f)
        Service.stopService(self)
        blinker.signal('coldstar.castiel.service.stopped').send(self)

registerAdapter(CastielService, IAuthenticator, ICasService)