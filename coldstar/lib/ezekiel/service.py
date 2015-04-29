#!/usr/bin/env python
# -*- coding: utf-8 -*-
import blinker
import logging
import uuid
import time

from twisted.application.service import Service
from zope.interface import implementer

from coldstar.lib.excs import LockNotFound, SerializableBaseException
from .interfaces import ILockService, ITmpLockService


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
            'success': True,
            'object_id': self.object_id,
            'acquire': self.acquire_time,
            'expiration': self.expiration_time,
            'token': self.token.encode('hex'),
            'locker': self.locker,
        }


class LockAlreadyAcquired(SerializableBaseException):
    __slots__ = ['object_id', 'acquire_time', 'locker']

    def __init__(self, lock):
        self.object_id = lock.object_id
        self.acquire_time = lock.acquire_time
        self.locker = lock.locker

    def __json__(self):
        return {
            'success': False,
            'object_id': self.object_id,
            'acquire': self.acquire_time,
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


class LockReleased(SerializableBaseException):
    __slots__ = ['object_id']

    def __init__(self, lock):
        self.object_id = lock.object_id

    def __json__(self):
        return {
            'success': True,
            'object_id': self.object_id
        }


boot = blinker.signal('coldstar:boot')
boot_ezekiel = blinker.signal('coldstar.lib.ezekiel:boot')

broadcast_gabriel = blinker.signal('coldstar.lib.gabriel:broadcast')


@implementer(ILockService, ITmpLockService)
class EzekielService(Service):
    short_timeout = 60
    long_timeout = 3600

    def __init__(self, config):
        self.short_timeout = config.get('short_timeout', 60)
        self.long_timeout = config.get('long_timeout', 3600)
        self.__locks = {}
        self.cas = None
        boot.connect(self.boot)

    def __acquire_lock(self, object_id, locker, short):
        logging.info('Acquiring lock %s', object_id)
        if object_id in self.__locks:
            return LockAlreadyAcquired(self.__locks[object_id][0])
        t = time.time()
        token = uuid.uuid4().bytes
        if short:
            from twisted.internet import reactor
            timeout = self.short_timeout if short else None
            lock = Lock(object_id, t, t + timeout, token, locker)
            delayed_call = reactor.callLater(timeout, self.release_lock, object_id, token)
        else:
            lock = Lock(object_id, t, None, token, locker)
            delayed_call = None
        self.__locks[object_id] = (lock, delayed_call)
        logging.info('Lock acquired')
        blinker.signal('coldstar.lib.ezekiel.lock.acquired').send(self, lock=lock)
        broadcast_gabriel.send(self, uri='coldstar.lib.ezekiel.lock.acquired', data=LockInfo(lock))
        return lock

    def acquire_lock(self, object_id, locker):
        return self.__acquire_lock(object_id, locker, False)

    def acquire_tmp_lock(self, object_id, locker):
        return self.__acquire_lock(object_id, locker, True)

    def release_lock(self, object_id, token):
        if object_id in self.__locks:
            lock, delayed_call = self.__locks[object_id]
            if lock.token == token:
                del self.__locks[object_id]
                if delayed_call and delayed_call.active():
                    delayed_call.cancel()
                blinker.signal('coldstar.lib.ezekiel.lock.released').send(self, lock=lock)
                broadcast_gabriel.send(self, uri='coldstar.lib.ezekiel.lock.released', data=LockInfo(lock))
                return LockReleased(lock)
            raise LockNotFound(object_id)
        raise LockNotFound(object_id)

    def prolong_tmp_lock(self, object_id, token):
        if object_id in self.__locks:
            lock, timeout = self.__locks[object_id]
            if lock.token == token:
                lock.expiration_time = time.time() + self.short_timeout
                if timeout:
                    timeout.reset(self.short_timeout)
                return lock
            raise LockAlreadyAcquired(lock)
        raise LockNotFound(object_id)

    def boot(self, root):
        print 'Ezekiel: boot...'
        self.setServiceParent(root)
        boot_ezekiel.send(self)

