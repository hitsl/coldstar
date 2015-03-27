# -*- coding: utf-8 -*-
from functools import wraps
from twisted.internet import defer

__author__ = 'mmalkov'


def deferred_to_thread(func):
    from twisted.internet.threads import deferToThread

    @wraps(func)
    def wrapper(*args, **kwargs):
        return deferToThread(func, *args, **kwargs)

    return wrapper


def run_in_thread(func):
    from twisted.internet.threads import deferToThread

    @wraps(func)
    @defer.inlineCallbacks
    def wrapper(*args, **kwargs):
        result = yield deferToThread(func, *args, **kwargs)
        defer.returnValue(result)

    return wrapper


class DeferredGroup(object):
    def __init__(self):
        self.deferred = defer.Deferred()
        self.__deferreds = {}
        self.__results = {}
        self.__errors = {}
        self.consume_errors = False
        self.fail_if_errors = False
        self.instant_fail = False

    def __check_finished(self):
        from twisted.internet import reactor
        if not self.__deferreds:
            if self.fail_if_errors and self.__errors:
                reactor.callLater(self.deferred.errback, self.__errors)
            else:
                reactor.callLater(self.deferred.callback, self.__results)

    @property
    def results(self):
        return self.__results

    @property
    def errors(self):
        return self.__errors

    def add(self, name, deferred):
        if name in self.__deferreds:
            raise Exception('Duplicate name')
        self.__deferreds[name] = deferred

        def __cb(result):
            del self.__deferreds[name]
            self.__results[name] = result
            self.__check_finished()
            return result

        def __eb(failure):
            del self.__deferreds[name]
            self.__results[name] = failure
            if self.instant_fail:
                self.cancel()
            self.__check_finished()
            if not self.consume_errors:
                return failure

        deferred.addCallbacks(__cb, __eb)

    def cancel(self):
        for deferred in self.__deferreds.itervalues():
            deferred.cancel()
        self.__deferreds = {}

    def wait(self):
        self.__check_finished()
        return self.deferred


def chain_deferreds(host, chainee):
    def _cb(result):
        chainee.callback(result)
        return result

    def _eb(failure):
        chainee.errback(failure)
        return failure

    host.addCallbacks(_cb, _eb)