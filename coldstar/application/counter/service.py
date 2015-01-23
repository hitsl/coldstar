# -*- coding: utf-8 -*-
import datetime
import logging
import re
import traceback
from twisted.application.service import Service
from twisted.python.components import registerAdapter
from zope.interface import implementer
from coldstar.lib.db.interfaces import IDataBaseService
from .interfaces import ICounterService

__author__ = 'viruzzz-kun'

logger = logging.getLogger()
re_exec = re.compile(ur'^\s*(?P<name>\w+?)\s*\((?P<arg>.*)\)\s*$')
re_date = re.compile(ur'(yyyy|yy|MM|dd)')


def _replace(match):
    return {
        'yyyy': '%Y',
        'yy': '%y',
        'MM': '%m',
        'dd': '%d',
    }.get(match.string, match.string)


def get_date_prefix(val):
    try:
        return datetime.date.today().strftime(re_date.sub(_replace, val))
    except ValueError:
        traceback.print_exc()
        return None


@implementer(ICounterService)
class CounterService(Service):
    db = None

    def __init__(self, db_service):
        self.db = db_service

    def acquire(self, counter_id, client_id=None):
        """Формирование externalId (номер обращения/истории болезни)."""
        from .models import rbCounter, ClientIdentification, rbAccountingSystem

        with self.db.context_session() as session:
            try:
                counter = session.query(rbCounter).get(counter_id)
            except:
                return ''

            def get_id_prefix(val):
                if not val:
                    return str(client_id)
                ext_val = session.query(ClientIdentification) \
                    .join(rbAccountingSystem) \
                    .filter(
                        ClientIdentification.client_id == client_id,
                        rbAccountingSystem.code == val
                    ).first()
                return ext_val.identifier if ext_val else None

            prefix_types = {
                'date': get_date_prefix,
                'id': get_id_prefix if client_id else lambda val: '',
            }

            prefix = []
            for p in counter.prefix .split(';'):
                m = re_exec.match(p).groupdict()
                if 'name' in m and m['name'] in prefix_types:
                    value = prefix_types[m['name']](m['arg'])
                    if value:
                        prefix.append(value)
            external_id = counter.separator.join(prefix + [str(counter.value + 1)])

            counter.value += 1
            session.add(counter)
            session.commit()
            # session.rollback()
            return external_id

registerAdapter(CounterService, IDataBaseService, ICounterService)