# -*- coding: utf-8 -*-
from libcastiel.interfaces import IAuthTokenObject
import os
from zope.interface import implementer

__author__ = 'viruzzz-kun'


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


