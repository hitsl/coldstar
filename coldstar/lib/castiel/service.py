# -*- coding: utf-8 -*-
from UserDict import UserDict
import time

import os
import msgpack
import blinker
from twisted.python import failure
from twisted.python.components import registerAdapter
from twisted.application.service import Service
from twisted.internet import defer
from twisted.internet.task import LoopingCall

from zope.interface import implementer
from coldstar.lib import msgpack_helpers
from coldstar.lib.castiel.interfaces import IAuthenticator
from .exceptions import EExpiredToken, ETokenAlreadyAcquired
from .interfaces import ICasService, IAuthTokenObject


__author__ = 'mmalkov'


boot = blinker.signal('coldstar.boot')
cas_boot = blinker.signal('coldstar.lib.castiel.boot')
auth_boot = blinker.signal('coldstar.lib.auth.boot')


@implementer(IAuthTokenObject)
class AuthTokenObject(object):
    __slots__ = ['token', 'deadline', 'object']

    def __init__(self, obj, deadline, token=None):
        self.token = os.urandom(16) if token is None else token
        self.deadline = deadline
        self.object = obj

    @property
    def user_id(self):
        return self.object.user_id


class CastielUserRegistry(UserDict):
    msgpack = 1

    def __getstate__(self):
        return [
            (ato.token, ato.deadline, ato.object)
            for ato in self.data.itervalues()
        ]

    def __setstate__(self, state):
        self.data = dict(
            (token, AuthTokenObject(obj, deadline, token))
            for (token, deadline, obj) in state
        )


@implementer(ICasService)
class CastielService(Service):
    expiry_time = 3600
    clean_period = 10
    check_duplicate_tokens = False
    cors_domain = 'http://127.0.0.1:5000'
    cookie_domain = '127.0.0.1'

    def __init__(self):
        self.auth = None
        self.tokens = CastielUserRegistry()
        self.expired_cleaner = None
        boot.connect(self.bootstrap_cas)
        auth_boot.connect(self.auth_boot)

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
            ato = self.tokens[token] = AuthTokenObject(user, deadline, token)  # (deadline, user_id)
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
        return ato.object

    def startService(self):
        try:
            with open('tokens.msgpack', 'rb') as f:
                self.tokens = msgpack_helpers.load(f.read())
        except (IOError, OSError, msgpack.UnpackException, msgpack.UnpackValueError):
            pass
        self.expired_cleaner = LoopingCall(self._clean_expired)
        self.expired_cleaner.start(self.clean_period)
        Service.startService(self)
        blinker.signal('coldstar.castiel.service.started').send(self)

    def stopService(self):
        self.expired_cleaner.stop()
        with open('tokens.msgpack', 'wb') as f:
            f.write(msgpack_helpers.dump(self.tokens))
        Service.stopService(self)
        blinker.signal('coldstar.castiel.service.stopped').send(self)

    def bootstrap_cas(self, root):
        self.setServiceParent(root)
        cas_boot.send(self)

    def auth_boot(self, sender):
        self.auth = sender

registerAdapter(CastielService, IAuthenticator, ICasService)