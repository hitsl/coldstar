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
    __slots__ = ['object_id', 'acquire_time', 'expiration_time', 'token', 'locker']

    def __init__(self, object_id, acquire_time, expiration_time, token, locker):
        self.object_id = object_id
        self.acquire_time = int(acquire_time)
        self.expiration_time = int(expiration_time)
        self.token = token
        self.locker = locker

    def __json__(self):
        return {
            'object_id': self.object_id,
            'acquire': self.acquire_time,
            'expiration': self.expiration_time,
            'token': self.token.encode('hex'),
            'locker': self.locker,
        }


class LockInfo(object):
    __slots__ = ['object_id', 'acquire_time', 'locker']

    def __init__(self, lock):
        self.object_id = lock.object_id
        self.acquire_time = lock.acquire_time
        self.locker = lock.locker

    def __json__(self):
        return {
            'object_id': self.object_id,
            'acquire': self.acquire_time,
            'locker': self.locker,
        }


@implementer(IColdStarService)
class ColdStarService(Service):
    def __init__(self):
        self.__locks = {}
        self.__timeouts = {}

    def acquire_lock(self, object_id, locker):
        if object_id in self.__locks:
            return LockInfo(self.__locks[object_id])
        lock = Lock(object_id, time.time(), None, uuid.uuid4().bytes, locker)
        self.__locks[object_id] = lock
        return lock

    def release_lock(self, object_id, token):
        if object_id in self.__locks:
            lock = self.__locks[object_id]
            if lock.token == token:
                del self.__locks[object_id]
                self.__timeouts.pop(object_id, None)
                return True
            return LockInfo(lock)
        return False

    def acquire_tmp_lock(self, object_id, locker):
        from twisted.internet import reactor
        if object_id in self.__locks:
            return LockInfo(self.__locks[object_id])
        t = time.time()
        token = uuid.uuid4().bytes
        lock = Lock(object_id, t, t + 60, token, locker)
        self.__locks[object_id] = lock
        self.__timeouts[object_id] = reactor.callLater(60, self.release_lock, object_id, token)
        return lock

    def prolong_tmp_lock(self, object_id, token):
        if object_id in self.__timeouts:
            lock = self.__locks[object_id]
            timeout = self.__timeouts[object_id]
            if lock.token == token:
                lock.expiration_time = time.time() + 60
                timeout.reset(60)
                return True
            return LockInfo(lock)
        return False


