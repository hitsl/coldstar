#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid
import time

from twisted.application.service import MultiService
from zope.interface import implementer
from coldstar.excs import LockNotFound

from coldstar.interfaces import ILockService, ITmpLockService


__author__ = 'viruzzz-kun'
__created__ = '13.09.2014'


class Lock(object):
    __slots__ = ['object_id', 'acquire_time', 'expiration_time', 'token', 'locker']

    def __init__(self, object_id, acquire_time, expiration_time, token, locker):
        self.object_id = object_id
        self.acquire_time = int(acquire_time)
        self.expiration_time = int(expiration_time) if isinstance(expiration_time, float) else expiration_time
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


class LockReleased(object):
    __slots__ = ['object_id']

    def __init__(self, lock):
        self.object_id = lock.object_id

    def __json__(self):
        return {
            'object_id': self.object_id
        }


@implementer(ILockService, ITmpLockService)
class ColdStarService(MultiService):
    short_timeout = 60
    long_timeout = 3600

    def __init__(self):
        MultiService.__init__(self)
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
                timeout = self.__timeouts.pop(object_id, None)
                if timeout and timeout.active():
                    timeout.cancel()
                return LockReleased(lock)
            return LockNotFound(object_id)
        raise LockNotFound(object_id)

    def acquire_tmp_lock(self, object_id, locker):
        from twisted.internet import reactor
        if object_id in self.__locks:
            return LockInfo(self.__locks[object_id])
        t = time.time()
        token = uuid.uuid4().bytes
        lock = Lock(object_id, t, t + self.short_timeout, token, locker)
        self.__locks[object_id] = lock
        self.__timeouts[object_id] = reactor.callLater(self.short_timeout, self.release_lock, object_id, token)
        return lock

    def prolong_tmp_lock(self, object_id, token):
        if object_id in self.__timeouts:
            lock = self.__locks[object_id]
            timeout = self.__timeouts[object_id]
            if lock.token == token:
                lock.expiration_time = time.time() + self.short_timeout
                timeout.reset(self.short_timeout)
                return lock
            return LockInfo(lock)
        raise LockNotFound(object_id)
