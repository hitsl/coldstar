#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid
from twisted.application.service import Service
import time

from zope.interface import implementer
from coldstar.interfaces import IColdStarService


__author__ = 'viruzzz-kun'
__created__ = '13.09.2014'


class Lock(object):
    __slots__ = ['acquire_time', 'expiration_time', 'token', 'locker']

    def __init__(self, acquire_time, expiration_time, token, locker):
        self.acquire_time = int(acquire_time)
        self.expiration_time = int(expiration_time)
        self.token = token
        self.locker = locker

    def __json__(self):
        return {
            'acquire': self.acquire_time,
            'expiration': self.expiration_time,
            'token': self.token,
            'locker': self.locker,
        }


class LockInfo(object):
    __slots__ = ['acquire_time', 'locker']

    def __init__(self, lock):
        self.acquire_time = lock.acquire_time
        self.locker = lock.locker

    def __json__(self):
        return {
            'acquire': self.acquire_time,
            'locker': self.locker,
        }


@implementer(IColdStarService)
class ColdStarService(Service):
    def __init__(self):
        self.__locks = {}
        self.__tokens = {}

    def acquire_lock(self, object_id, locker):
        if object_id in self.__locks:
            return LockInfo(self.__locks[object_id])
        return Lock(time.time(), None, uuid.uuid4().bytes, locker)

    def release_lock(self, object_id, token):
        if object_id in self.__locks:
            lock = self.__locks[object_id]
            if lock.token == token:
                del self.__locks[object_id]
                return True
            return LockInfo(lock)
        return False

    def acquire_tmp_lock(self, object_id, locker):
        if object_id in self.__locks:
            return LockInfo(self.__locks[object_id])
        t = time.time()
        return Lock(t, t + 60, uuid.uuid4().bytes, locker)

    def prolong_tmp_lock(self, object_id, token):
        if object_id in self.__locks:
            lock = self.__locks[object_id]
            if lock.token == token:
                lock.expiration_time = time.time() + 60
                return True
            return LockInfo(lock)
        return False


