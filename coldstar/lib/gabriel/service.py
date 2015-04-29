# -*- coding: utf-8 -*-
import collections
import blinker
from weakref import WeakSet
from coldstar.lib.gabriel.excs import NoSuchMethod, MethodAlreadyRegistered, MethodUriMismatch
from twisted.application.service import Service

__author__ = 'viruzzz-kun'


boot = blinker.signal('coldstar:boot')
boot_gabriel = blinker.signal('coldstar.lib.gabriel:boot')

broadcast_gabriel = blinker.signal('coldstar.lib.gabriel:broadcast')


class GabrielService(Service):
    def __init__(self, config):
        self.functions = {}
        self.subscriptions = collections.defaultdict(WeakSet)
        self.eager_subs = WeakSet()
        boot.connect(self.boot)
        broadcast_gabriel.connect(self.signal_broadcast)

    # Remote functions

    def register_function(self, uri, function):
        if uri in self.functions:
            raise MethodAlreadyRegistered(uri)
        self.functions[uri] = function

    def unregister_function(self, uri, function=None):
        if uri not in self.functions:
            raise NoSuchMethod(uri)
        if function is not None and function != self.functions[uri]:
            raise MethodUriMismatch(uri)
        del self.functions[uri]

    def call(self, uri, *args, **kwargs):
        if uri not in self.functions:
            raise NoSuchMethod(uri)
        return self.functions[uri](*args, **kwargs)

    # PubSub functions

    def subscribe(self, uri, callback):
        if uri is None:
            self.eager_subs.add(callback)
        else:
            self.subscriptions[uri].add(callback)

    def unsubscribe(self, uri, callback):
        if uri is None:
            self.eager_subs.discard(callback)
        else:
            self.subscriptions[uri].discard(callback)

    def broadcast(self, uri, data):
        for callback in self.subscriptions[uri]:
            callback(data)
        for callback in self.eager_subs:
            callback(uri, data)

    def signal_broadcast(self, sender, uri, data):
        self.broadcast(uri, data)

    # internal

    def boot(self, root):
        print 'Gabriel: boot...'
        self.setServiceParent(root)
        boot_gabriel.send(self)
