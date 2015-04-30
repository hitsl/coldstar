# -*- coding: utf-8 -*-
import collections
import re
import blinker
from weakref import WeakSet
from coldstar.lib.gabriel.excs import NoSuchMethod, MethodAlreadyRegistered, MethodUriMismatch
from twisted.application.service import Service
from twisted.internet import reactor

__author__ = 'viruzzz-kun'


boot = blinker.signal('coldstar:boot')
boot_gabriel = blinker.signal('coldstar.lib.gabriel:boot')

broadcast_gabriel = blinker.signal('coldstar.lib.gabriel:broadcast')
gabriel_session_connected = blinker.signal('coldstar.lib.gabriel:session:connected')
gabriel_session_disconnected = blinker.signal('coldstar.lib.gabriel:session:disconnected')
gabriel_private_message = blinker.signal('coldstar.lib.gabriel:private')

re_private = re.compile(ur'^private:(?P<uid>.+):(?P<uri>.*)$', re.X | re.U)


class GabrielService(Service):
    def __init__(self, config):
        self.functions = {}
        self.subscriptions = collections.defaultdict(WeakSet)
        self.sessions = collections.defaultdict(WeakSet)
        boot.connect(self.boot)
        broadcast_gabriel.connect(self.signal_broadcast)

    # Session functions

    def register_session(self, user_id, session):
        self.sessions[unicode(user_id)].add(session)
        reactor.callLater(0, gabriel_session_connected.send, session)
        print 'Session %r for user "%s" registered' % (session, user_id)

    def unregister_session(self, user_id, session):
        self.sessions[unicode(user_id)].discard(session)
        print 'Session %r for user "%s" unregistered' % (session, user_id)

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
        self.subscriptions[uri].add(callback)

    def unsubscribe(self, uri, callback):
        if uri is None:
            self.eager_subs.discard(callback)
        else:
            self.subscriptions[uri].discard(callback)

    def broadcast(self, uri, data):
        for callback in self.subscriptions[uri]:
            callback(data)
        if uri.startswith('private:'):
            match = re_private.match(uri)
            user_id = match.group(1)
            gabriel_private_message.send(None, uri=uri, user_id=user_id, data=data)
            for session in self.sessions.get(user_id):
                session.system_broadcast(uri, data)
        else:
            for user_id, sessions in self.sessions.iteritems():
                for session in sessions:
                    session.system_broadcast(uri, data)

    def signal_broadcast(self, sender, uri, data):
        self.broadcast(uri, data)

    # internal

    def boot(self, root):
        print 'Gabriel: boot...'
        self.setServiceParent(root)
        boot_gabriel.send(self)
