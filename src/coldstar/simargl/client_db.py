# -*- coding: utf-8 -*-
import json
from libcoldstar.plugin_helpers import Dependency
from libsimargl.client import SimarglClient
from libsimargl.message import Message
from sqlalchemy import Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

__author__ = 'viruzzz-kun'


Base = declarative_base()
metadata = Base.metadata


class SimarglMessageModel(Base):
    __tablename__ = "SimarglMessages"

    id = Column(Integer, primary_key=True, nullable=False)
    sender = Column(Integer)
    recipient = Column(Integer)
    tags_ = Column("tags", Text)
    data_ = Column("data", Text)

    @property
    def tags(self):
        return json.loads(self.tags_)

    @tags.setter
    def tags(self, value):
        self.tags_ = json.dumps(value)

    @property
    def data(self):
        return json.loads(self.data_)

    @data.setter
    def data(self, value):
        self.data_ = json.dumps(value)

    def from_message(self, message):
        self.sender = message.sender
        self.recipient = message.recipient
        self.tags = sorted(message.tags)
        self.data = message.data

    def as_message(self):
        message = Message()
        message.immediate = False
        message.sender = self.sender
        message.recipient = self.recipient
        message.tags = set(self.tags)
        message.data = self.data


class Client(SimarglClient):
    db = Dependency('coldstar.db')

    def send(self, message):
        """
        :type message: libsimargl.message.Message
        :param message:
        :return:
        """
        if message.immediate or message.secondary:
            return
        with self.db.context_session() as session:
            obj = SimarglMessageModel()
            obj.from_message(message)
            session.add(obj)
