# -*- coding: utf-8 -*-
import json
import datetime
import blinker
from coldstar.lib.twisted_helpers import deferred_to_thread
from coldstar.lib.gabriel_.interfaces import IUserNotifications
from coldstar.lib.utils import transfer_fields, as_json
from sqlalchemy import Column, Integer, Text, SmallInteger, DateTime, or_, String
from sqlalchemy.ext.declarative import declarative_base
from twisted.python.components import registerAdapter
from zope.interface import implementer

__author__ = 'viruzzz-kun'


Base = declarative_base()
metadata = Base.metadata


boot = blinker.signal('coldstar:boot')
boot_db = blinker.signal('coldstar.lib.db:boot')
boot_self = blinker.signal('coldstar.lib.gabriel.persist:boot')
boot_gabriel = blinker.signal('coldstar.lib.gabriel:boot')
gabriel_session_connected = blinker.signal('coldstar.lib.gabriel:session:connected')
gabriel_session_disconnected = blinker.signal('coldstar.lib.gabriel:session:disconnected')
gabriel_private_message = blinker.signal('coldstar.lib.gabriel:private')


class UserNotifications(Base):
    __tablename__ = 'UserNotifications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, default=None)
    datetime = Column(DateTime)
    read = Column(SmallInteger, default=0)
    uri = Column(String(1024))
    data_ = Column('data', Text)

    @property
    def data(self):
        return json.loads(self.data_)

    @data.setter
    def data(self, value):
        self.data_ = as_json(value)


@implementer(IUserNotifications)
class UserNotificationsAdaptor(object):
    __slots__ = ['id', 'user_id', 'datetime', 'read', 'uri', 'data']

    def __init__(self, un):
        transfer_fields(self, un, self.__slots__)


registerAdapter(UserNotificationsAdaptor, UserNotifications, IUserNotifications)


class MisUserNotifications(object):
    def __init__(self):
        self.db = None
        self.gabriel = None
        boot.connect(self.boot)
        boot_db.connect(self.boot_db)
        boot_gabriel.connect(self.boot_gabriel)
        gabriel_session_connected.connect(self.new_session)
        gabriel_private_message.connect(self.private_message)

    def boot(self, root):
        print 'Gabriel MIS Connection: boot...'
        boot_self.send(self)

    def boot_db(self, db):
        print 'Gabriel MIS Connection: Database connected'
        self.db = db

    def boot_gabriel(self, gabriel):
        print 'Gabriel MIS Connection: Gabriel connected'
        self.gabriel = gabriel

    def new_session(self, session):
        def send_notifications(notifications):
            for n in notifications:
                session.system_broadcast(n.uri, n.data)
        self.get_notifications(session.user_id).addCallback(send_notifications)

    def private_message(self, _, user_id, uri, data):
        self.store_notification(user_id, uri, data)

    @deferred_to_thread
    def get_notifications(self, user_id):
        with self.db.context_session(1) as session:
            query = session.query(UserNotifications).filter(
                or_(
                    UserNotifications.user_id.is_(None),
                    UserNotifications.user_id == user_id,
                ), UserNotifications.read == 0
            ).order_by(UserNotifications.datetime.asc())
            return map(IUserNotifications, query.all())

    @deferred_to_thread
    def store_notification(self, user_id, uri, data):
        with self.db.context_session(0) as session:
            o = UserNotifications()
            o.datetime = datetime.datetime.now()
            o.user_id = user_id
            o.data = data
            o.uri = uri
            session.add(o)


def make(config):
    return MisUserNotifications()