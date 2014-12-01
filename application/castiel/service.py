# -*- coding: utf-8 -*-
import os
import time
from twisted.application.service import Service
from zope.interface import implementer
from application.castiel.interfaces import ICasService

__author__ = 'mmalkov'


@implementer(ICasService)
class CastielService(Service):
    rot_time = 3600

    def __init__(self):
        self.tokens = {}

    def acquire_token(self, login, password):
        # TODO: ask database
        ctime = time.time()
        token = os.urandom(16)
        self.tokens[token] = ctime + self.rot_time
        return token

    def release_token(self, token):
        if token in self.tokens:
            del self.tokens[token]
            return True
        else:
            return False

    def check_token(self, token):
        return token in self.tokens and self.tokens[token] > time.time()

    def prolong_token(self, token):
        if token not in self.tokens:
            return False
        self.tokens[token] = time.time() + self.rot_time
        return True
