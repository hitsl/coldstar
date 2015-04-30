# -*- coding: utf-8 -*-
import collections
import blinker
from .interfaces import IUserSession

__author__ = 'viruzzz-kun'


boot = blinker.signal('coldstar:boot')
boot_cas = blinker.signal('coldstar.lib.castiel:boot')
boot_self = blinker.signal('coldstar.lib.gabriel.session:boot')


class Session(object):
    session_manager = None
    transport = None
    user_id = None

    def __init__(self, transport):
        self.transport = transport

    def authenticate(self, user_id):
        self.user_id = user_id

    def client_broadcast(self, uri, data):
        pass

    def client_subscribe(self, uri):
        pass

    def client_unsubscribe(self, uri):
        pass

    def client_call(self, uri, *args, **kwargs):
        pass

    def start(self):
        pass

    def stop(self):
        pass


class SessionManager(object):
    def __init__(self):
        self.user_sessions = collections.defaultdict(set)
        self.app_sessions = collections.defaultdict(set)
        self.cas = None

    def get_session(self, transport):
        return IUserSession(transport)

    def session_started(self, session):
        self.user_sessions[session.user_id].add(session)