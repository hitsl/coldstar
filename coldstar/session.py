#!/usr/bin/env python
# -*- coding: utf-8 -*-
from twisted.python.components import registerAdapter
from zope.interface import implementer
from coldstar.excs import LockNotFound, LockerNotSet
from coldstar.interfaces import ILockSession, ILockService
from coldstar.service import Lock

__author__ = 'viruzzz-kun'
__created__ = '15.10.2014'


@implementer(ILockSession)
class ColdStarSession(object):
    def __init__(self, service):
        self.service = service
        self.locks = {}
        self.locker = None

    def start_session(self, locker):
        self.locker = locker
        return locker

    def close_session(self):
        for object_id, lock in self.locks.iteritems():
            self.service.release_lock(object_id, lock.token)

    def acquire_lock(self, object_id):
        if not self.locker:
            raise LockerNotSet()
        lock = self.service.acquire_lock(object_id, self.locker)
        if isinstance(lock, Lock):
            self.locks[lock.object_id] = lock
        return lock

    def release_lock(self, object_id):
        if object_id not in self.locks:
            raise LockNotFound(object_id)
        lock = self.locks.pop(object_id)
        return self.service.release_lock(object_id, lock.token)

registerAdapter(ColdStarSession, ILockService, ILockSession)