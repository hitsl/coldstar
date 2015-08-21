# -*- coding: utf-8 -*-
import datetime
from libcoldstar.plugin_helpers import Dependency
from libsimargl.client import SimarglClient
from libsimargl.message import Message
from sqlalchemy import Column, Integer, Text, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from twisted.internet.threads import deferToThread


Base = declarative_base()
metadata = Base.metadata


class Errand(Base):
    __tablename__ = u'Errand'
    _table_description = u'поручения'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False, default=datetime.datetime.now)
    modifyDatetime = Column(DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    number = Column(String(30), nullable=False)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    setPerson_id = Column(index=True)
    execPerson_id = Column(index=True)
    text = Column(Text, nullable=False)
    plannedExecDate = Column(DateTime, nullable=False)
    execDate = Column(DateTime, nullable=False)
    event_id = Column(Integer, index=True)
    result = Column(Text, nullable=False)
    readingDate = Column(DateTime)
    status_id = Column(Integer, nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'create_datetime': self.createDatetime,
            'number': self.number,
            'set_person': self.setPerson,
            'exec_person': self.execPerson,
            'text': self.text,
            'planned_exec_date': self.plannedExecDate,
            'exec_date': self.execDate,
            'result': self.result,
            'reading_date': self.readingDate
        }

    def from_message(self, message, number):
        self.setPerson_id = message.sender
        self.execPerson_id = message.recipient
        self.text = message.data.get('text', '')
        self.number = number
        self.event_id = message.data.get('event_id', '')
        self.plannedExecDate = message.data.get('planned_exec_date', datetime.datetime.now())

    def as_message(self):
        message = Message()
        message.topic = 'errand'
        message.sender = self.setPerson_id
        message.recipient = self.execPerson_id
        message.tags = set()
        message.data = {
            'text': self.text
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
        if message.control and message.topic == 'errand:new':
            return self.new_mail(message)

    def new_mail(self, message):
        def worker_single():
            with self.db.context_session() as session:
                obj = Errand()
                number = get_new_errand_number(session)
                obj.from_message(message, number)
                session.add(obj)
            return obj.id

        def worker_envelope():
            result = []
            with self.db.context_session() as session:
                for msg in message.data:
                    obj = Errand()
                    obj.from_message(msg)
                    session.add(obj)
                    result.append(obj)

        if message.envelope:
            deferToThread(worker_envelope)
        else:
            deferToThread(worker_single)


class rbCounter(Base):
    __tablename__ = u'rbCounter'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False)
    name = Column(String(64), nullable=False)
    value = Column(Integer, nullable=False, server_default=u"'0'")
    prefix = Column(String(32))
    separator = Column(String(8), server_default=u"' '")
    reset = Column(Integer, nullable=False, server_default=u"'0'")
    startDate = Column(DateTime, nullable=False)
    resetDate = Column(DateTime)
    sequenceFlag = Column(Integer, nullable=False, server_default=u"'0'")


def get_new_errand_number(session):
    """Формирование number (номера поручения)."""
    counter = session.query(rbCounter).filter(rbCounter.code == 8).with_for_update().first()
    if not counter:
        return ''
    external_id = _get_errand_number_from_counter(counter.prefix,
                                                  counter.value + 1,
                                                  counter.separator)
    counter.value += 1
    session.add(counter)
    return external_id


def _get_errand_number_from_counter(prefix, value, separator):
    def get_date_prefix(val):
        val = val.replace('Y', 'y').replace('m', 'M').replace('D', 'd')
        if val.count('y') not in [0, 2, 4] or val.count('M') > 2 or val.count('d') > 2:
            return None
        # qt -> python date format
        _map = {'yyyy': '%Y', 'yy': '%y', 'mm': '%m', 'dd': '%d'}
        try:
            format_ = _map.get(val, '%Y')
            date_val = datetime.date.today().strftime(format_)
            check = datetime.datetime.strptime(date_val, format_)
        except ValueError, e:
            return None
        return date_val

    prefix_types = {'date': get_date_prefix}

    prefix_parts = prefix.split(';')
    prefix = []
    for p in prefix_parts:
        for t in prefix_types:
            pos = p.find(t)
            if pos == 0:
                val = p[len(t):]
                if val.startswith('(') and val.endswith(')'):
                    val = prefix_types[t](val[1:-1])
                    if val:
                        prefix.append(val)
    return separator.join(prefix + ['%d' % value])