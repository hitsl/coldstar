# -*- coding: utf-8 -*-
import time

from UserDict import UserDict
from libcoldstar.plugin_helpers import Dependency, ColdstarPlugin
import os
import msgpack
from twisted.python import failure
from twisted.python.components import registerAdapter
from twisted.application.service import Service
from twisted.internet import defer
from twisted.internet.task import LoopingCall
from zope.interface import implementer
from libcoldstar import msgpack_helpers
from libcastiel.objects import AuthTokenObject
from libcastiel.exceptions import EExpiredToken, ETokenAlreadyAcquired
from libcastiel.interfaces import ICasService, IAuthenticator

__author__ = 'mmalkov'


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
class CastielService(Service, ColdstarPlugin):
    signal_name = 'coldstar.castiel'
    expiry_time = 3600
    clean_period = 10
    check_duplicate_tokens = False
    cors_domain = 'http://127.0.0.1:5000'
    cookie_domain = '127.0.0.1'
    root = Dependency('coldstar')
    auth = Dependency('libcoldstar.auth')

    def __init__(self):
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
            ato = self.tokens[token] = AuthTokenObject(user, deadline, token)  # (deadline, user_id)
            return ato

        d = self.auth.get_user(login, password)
        d.addCallback(_cb)
        return d

    def release_token(self, token):
        if token in self.tokens:
            ato = self.tokens[token]
            del self.tokens[token]
            return defer.succeed(True)
        return defer.fail(EExpiredToken(token))

    def check_token(self, token, prolong=False):
        if token not in self.tokens:
            return defer.fail(EExpiredToken(token))
        ato = self.tokens[token]
        if ato.deadline < time.time():
            return defer.fail(EExpiredToken(token))
        if prolong:
            self.prolong_token(token)
        return defer.succeed((ato.user_id, ato.deadline))

    def prolong_token(self, token):
        if token not in self.tokens:
            return defer.fail(EExpiredToken(token))
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
                del self.tokens[token]

    def get_user_quick(self, token):
        """
        Returns users Auth Token Object
        :param token: Auth token
        :rtype: AuthTokenObject
        :return:
        """
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

    def stopService(self):
        self.expired_cleaner.stop()
        with open('tokens.msgpack', 'wb') as f:
            f.write(msgpack_helpers.dump(self.tokens))
        Service.stopService(self)


registerAdapter(CastielService, IAuthenticator, ICasService)