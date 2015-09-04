# -*- coding: utf-8 -*-
import datetime
from libcoldstar.plugin_helpers import Dependency
from libsimargl.client import SimarglClient
from coldstar.errands.models import Errand, rbCounter
from twisted.internet.threads import deferToThread


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


