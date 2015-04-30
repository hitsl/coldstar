# -*- coding: utf-8 -*-
import collections
import blinker
from twisted.application.service import Service


__author__ = 'viruzzz-kun'

boot = blinker.signal('coldstar:boot')
boot_self = blinker.signal('coldstar.lib.gabriel:boot')
boot_persist = blinker.signal('coldstar.lib.gabriel.persist:boot')


class GabrielService(Service):
    def __init__(self, config):
        self.sessions = collections.defaultdict(set)
        self.persist = None
        boot.connect(self.boot)
        boot_persist.connect(self.boot_persist)

    def boot(self, root):
        print 'Gabriel: boot...'
        self.setServiceParent(root)
        boot_self.send(self)

    def boot_persist(self, persist):
        print 'Gabriel: persist connected'
        self.persist = persist

    def send_notification(self, user_id, data):
        if self.persist:
            self.persist.store_notification(user_id, data)
        if user_id and user_id in self.sessions:
            for session in self.sessions[user_id]:
                session.send(data)

    def install_session(self, user_id, session):
        self.sessions[user_id].add(session)

        def fire(messages):
            for message in messages:
                session.send(message)

        self.persist.get_notifications(user_id).addCallback(fire)

    def uninstall_session(self, user_id, session):
        self.sessions[user_id].discard(session)