# -*- coding: utf-8 -*-
from twisted.python.components import registerAdapter
from coldstar.lib.db.interfaces import IDataBaseService
from sqlalchemy import or_
from twisted.application.service import Service
from twisted.internet import defer, threads
from zope.interface import implementer

from coldstar.application.sage.interfaces import ISettingsService
from coldstar.lib.excs import SerializableBaseException


__author__ = 'viruzzz-kun'


class ENodeNotFound(SerializableBaseException):
    def __init__(self, name):
        self.message = u'Node "%s" not found' % name


def _safe_int(value):
    try:
        return int(value)
    except ValueError:
        return value


@implementer(ISettingsService)
class SettingsService(Service):
    def __init__(self, database_service):
        self.db = database_service

    @defer.inlineCallbacks
    def get_value(self, key, subtree):
        from .models import Settings

        def get_exact():
            with self.db.context_session(True) as session:
                result = session.query(Settings).filter(Settings.path == key).first()
                if result is not None:
                    return {
                        result.path: _safe_int(result.value)
                    }
                raise ENodeNotFound(key)

        def get_subtree():
            with self.db.context_session(True) as session:
                nodes = session.query(Settings).filter(or_(Settings.path.startswith(key + '.'), Settings.path == key)).all()
                if not nodes:
                    raise ENodeNotFound(key)
                return dict(
                    (r.path, _safe_int(r.value))
                    for r in nodes
                )

        if subtree:
            result = yield threads.deferToThread(get_subtree)
        else:
            result = yield threads.deferToThread(get_exact)

        defer.returnValue(result)

    @defer.inlineCallbacks
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

        yield threads.deferToThread(make)

registerAdapter(SettingsService, IDataBaseService, ISettingsService)