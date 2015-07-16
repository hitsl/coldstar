# -*- coding: utf-8 -*-
import json
import datetime
import blinker
from libcoldstar.plugin_helpers import Dependency
from libcoldstar.twisted_helpers import deferred_to_thread
from libsimargl.client import SimarglClient
from libsimargl.message import Message
from sqlalchemy import Column, Integer, Text, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

__author__ = 'viruzzz-kun'


Base = declarative_base()
metadata = Base.metadata


class UserMail(Base):
    __tablename__ = "UserMail"
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, nullable=True)
    recipient_id = Column(Integer, nullable=True)
    subject = Column(String(256), nullable=False)
    text = Column(Text, nullable=False)
    datetime = Column(DateTime, nullable=False)
    read = Column(Integer)
    mark = Column(Integer)
    parent_id = Column(Integer, nullable=True)
    folder = Column(String(50), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'subject': self.subject,
            'text': self.text,
        }

    def from_message(self, message):
        self.sender_id = message.sender
        self.recipient_id = message.recipient
        self.subject = message.data.get('subject', '')
        self.text = message.data.get('text', '')
        self.datetime = message.data.get('datetime', datetime.datetime.now())
        self.parent_id = message.data.get('parent_id', None)
        self.mark = message.data.get('mark') and 1 or 0
        self.folder = message.data.get('folder', 'inbox')
        self.read = 0

    def as_message(self):
        message = Message()
        message.topic = 'mail'
        message.sender = self.sender_id
        message.recipient = self.recipient_id
        message.tags = set()
        message.data = {
            'subject': self.subject,
            'text': self.text,
            'datetime': self.datetime,
            'read': self.read,
            'mark': self.mark,
            'parent_id': self.parent_id,
            'folder': self.folder,
        }
        return message


class Client(SimarglClient):
    db = Dependency('coldstar.db')

    def send(self, message):
        """
        :type message: libsimargl.message.Message
        :param message:
        :return:
        """
        if message.control and message.topic == 'mail:new':
            return self.new_mail(message)
        elif message.control and message.topic == 'mail:last':
            return self.get_mail(message)

    def new_mail(self, message):
        @deferred_to_thread
        def worker():
            with self.db.context_session() as session:
                obj = UserMail()
                obj.from_message(message)
                session.add(obj)
                return obj.id

        def on_finish(oid):
            result = Message()
            result.immediate = True
            result.secondary = True
            result.sender = message.sender
            result.recipient = message.recipient
            result.control = False
            result.magic = message.magic
            result.tags = message.tags
            result.topic = 'mail'
            result.data = {
                'id': oid
            }
            blinker.signal('simargl.client:message').send(self, message=result)

        worker().addCallback(on_finish)

    def get_mail(self, message):
        recipient = message.sender

        @deferred_to_thread
        def worker():
            if isinstance(message.data, dict):
                count = message.data.get('count', 10)
            else:
                count = 10
            message_list = []
            with self.db.context_session(True) as session:
                for mail in session.query(UserMail) \
                        .filter(UserMail.recipient_id == recipient) \
                        .order_by(UserMail.id.desc()) \
                        .limit(count):
                    msg = mail.as_message()
                    msg.secondary = True
                    message_list.append(msg)
            return message_list

        def on_finish(message_list):
            result = Message()
            result.secondary = True
            result.recipient = recipient
            result.topic = 'mail'
            result.envelope = True
            result.data = message_list
            result.immediate = True
            blinker.signal('simargl.client:message').send(self, message=result)

        worker().addCallback(on_finish)
