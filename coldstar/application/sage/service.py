# -*- coding: utf-8 -*-
from twisted.python.components import registerAdapter
from sqlalchemy import or_
from twisted.application.service import Service
from twisted.internet import threads
from zope.interface import implementer

from coldstar.lib.db.interfaces import IDataBaseService
from coldstar.application.sage.interfaces import ISettingsService
from coldstar.lib.excs import SerializableBaseException
from coldstar.lib.utils import safe_int


__author__ = 'viruzzz-kun'


class ENodeNotFound(SerializableBaseException):
    def __init__(self, name):
        self.message = u'Node "%s" not found' % name


@implementer(ISettingsService)
class SettingsService(Service):
    def __init__(self, database_service):
        self.db = database_service

    def get_value(self, key, subtree):
        from .models import Settings

        def get_exact():
            with self.db.context_session(True) as session:
                result = session.query(Settings).filter(Settings.path == key).first()
                if result is not None:
                    return {
                        result.path: safe_int(result.value)
                    }
                raise ENodeNotFound(key)

        def get_subtree():
            with self.db.context_session(True) as session:
                query = session.query(Settings)
                if key:
                    query = query.filter(or_(Settings.path.startswith(key + '.'), Settings.path == key))
                nodes = query.all()
                if not nodes:
                    raise ENodeNotFound(key)
                return dict(
                    (r.path, safe_int(r.value))
                    for r in nodes
                )

        if subtree:
            return threads.deferToThread(get_subtree)
        else:
            return threads.deferToThread(get_exact)

    def set_value(self, key, value):
        def make():
            with self.db.context_session(True) as session:
                from .models import Settings
                result = session.query(Settings).filter(Settings.path == key).first()
                if result is None:
                    result = Settings()
                    result.path = key
                result.value = value
                session.add(Settings)
                session.commit()

        return threads.deferToThread(make)

registerAdapter(SettingsService, IDataBaseService, ISettingsService)