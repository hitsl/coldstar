#!/usr/bin/env python
# -*- coding: utf-8 -*-
from coldstar.eventsource import make_event

from libcoldstar.plugin_helpers import ColdstarPlugin, Dependency
from libcoldstar.utils import safe_int
from twisted.internet.task import LoopingCall
from twisted.python import log
from twisted.python import failure
from twisted.web.resource import IResource, Resource
from twisted.web.server import NOT_DONE_YET
from zope.interface import implementer
from .interfaces import IRestService

__author__ = 'viruzzz-kun'
__created__ = '05.10.2014'


class EventSourcedLock(object):
    keep_alive = False

    def __init__(self, object_id, locker, request, ezekiel):
        self.object_id = object_id
        self.locker = locker
        self.request = request
        self.ezekiel = ezekiel
        self.lock = None
        self.lc = None
        self.ka = LoopingCall(self.request.write, make_event(None, 'ping'))

    def try_acquire(self):
        lock = self.ezekiel.acquire_lock(self.object_id, self.locker)
        if hasattr(lock, 'token'):
            self.lock = lock
            self.request.write(make_event(lock, 'acquired'))
            self.lc.stop()
            self.lc = LoopingCall(self.try_prolong)
            self.lc.start(self.ezekiel.long_timeout / 2, False)
        else:
            self.request.write(make_event(lock, 'rejected'))

    def try_prolong(self):
        try:
            self.lock = self.ezekiel.prolong_tmp_lock(self.object_id, self.lock.token)
        except Exception as e:
            self.request.write(make_event(e, 'exception'))
            self.lock = None
            self.stop()
            self.request.finish()
        else:
            self.request.write(make_event(self.lock, 'prolonged'))

    def start(self):
        if isinstance(self.keep_alive, int):
            self.ka.start(self.keep_alive)
        self.lc = LoopingCall(self.try_acquire)
        self.lc.start(10)

    def stop(self):
        if self.lc:
            self.lc.stop()
        if self.ka.running:
            self.ka.stop()
        if self.lock:
            self.ezekiel.release_lock(self.object_id, self.lock.token)


@implementer(IResource, IRestService)
class EzekielEventSourceResource(Resource, ColdstarPlugin):
    signal_name = 'coldstar.ezekiel.eventsource'
    isLeaf = True

    service = Dependency('coldstar.ezekiel')
    cas = Dependency('coldstar.castiel')
    web = Dependency('libcoldstar.web')

    def __init__(self, config):
        Resource.__init__(self)
        self.keep_alive = safe_int(config.get('keep-alive', False))

    def render(self, request):
        """
        :type request: libcoldstar.web.wrappers.TemplatedRequest
        :param request:
        :return:
        """
        if self.web.crossdomain(request, True):
            return ''

        pp = filter(None, request.postpath)
        if len(pp) != 1:
            request.setResponseCode(404)
            return ''
        object_id = pp[0]

        ez_lock = []

        def onFinish(result):
            if ez_lock:
                ez_lock[0].stop()
            log.msg("Connection from %s closed" % request.getClientIP(), system="Ezekiel Event Source")
            if not isinstance(result, failure.Failure):
                return result

        def onUser(user_info):
            if isinstance(user_info, failure.Failure):
                request.setResponseCode(401, 'Authentication Failure')
                request.finish()
                return user_info
            else:
                request.user = user_info[0]
                request.setHeader('Content-Type', 'text/event-stream; charset=utf-8')
                request.write('')

                ezl = EventSourcedLock(object_id, user_info[0], request, self.service)
                ezl.keep_alive = self.keep_alive
                request.notifyFinish().addBoth(onFinish)
                ezl.start()
                ez_lock.append(ezl)
                log.msg("Connection from %s established" % request.getClientIP(), system="Ezekiel Event Source")

        token = request.getCookie('authToken')
        if not token:
            request.setResponseCode(401)
            return ''

        self.cas.check_token(token.decode('hex')).addBoth(onUser)
        return NOT_DONE_YET

    @web.on
    def boot_web(self, web):
        web.root_resource.putChild('ezekiel-es', self)


def make(config):
    return EzekielEventSourceResource(config)
