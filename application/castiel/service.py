# -*- coding: utf-8 -*-
import os
import time
from twisted.application.service import Service
from twisted.internet.task import LoopingCall
from zope.interface import implementer
from application.castiel.interfaces import ICasService
from application.coldstar.excs import SerializableBaseException

__author__ = 'mmalkov'


class ERottenToken(SerializableBaseException):
    def __init__(self, token):
        self.message = 'Token %s is expired' % token.encode('hex')


@implementer(ICasService)
class CastielService(Service):
    rot_time = 3600

    def __init__(self):
        self.tokens = {}
        self.rot_cleaner = LoopingCall(self._clean_rotten)

    def acquire_token(self, login, password):
        # TODO: ask database

        user_id = os.urandom(4)
        token = os.urandom(16)

        ctime = time.time()
        self.tokens[token] = (ctime + self.rot_time, user_id)
        return token

    def release_token(self, token):
        if token in self.tokens:
            del self.tokens[token]
            return True
        raise ERottenToken(token)

    def check_token(self, token):
        return token in self.tokens and self.tokens[token][0] > time.time()

    def prolong_token(self, token):
        if token not in self.tokens:
            raise ERottenToken(token)
        self.tokens[token] = (time.time() + self.rot_time, self.tokens[token][1])
        return True

    def _clean_rotten(self):
        now = time.time()
        for token, (t, _) in self.tokens.items():
            if t > now:
                del self.tokens[token]

    def startService(self):
        Service.startService(self)
        self.rot_cleaner.start(60)

    def stopService(self):
        Service.stopService(self)
        self.rot_cleaner.stop()