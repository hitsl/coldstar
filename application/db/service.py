# -*- coding: utf-8 -*-
import contextlib
import sqlalchemy
import sqlalchemy.orm
from twisted.application.service import Service
from zope.interface.declarations import implementer
from .interfaces import IDataBaseService

__author__ = 'mmalkov'


@implementer(IDataBaseService)
class DataBaseService(Service):
    def __init__(self, url):
        self.url = url
        self.db = None
        self.session = None

    def startService(self):
        Service.startService(self)
        self.db = sqlalchemy.create_engine(self.url)
        self.session = sqlalchemy.orm.sessionmaker(bind=self.db)

    def stopService(self):
        Service.startService(self)
        self.db = self.session = None

    def get_session(self):
        return self.Session()

    @contextlib.contextmanager
    def context_session(self, read_only=False):
        session = self.session()
        try:
            yield session
        except:
            session.rollback()
            raise
        else:
            if read_only:
                session.rollback()
            else:
                session.commit()
        finally:
            session.close()

