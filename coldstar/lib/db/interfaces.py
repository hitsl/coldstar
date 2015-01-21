# -*- coding: utf-8 -*-
from twisted.application.service import IService
from zope.interface import Attribute

__author__ = 'mmalkov'


class IDataBaseService(IService):
    db = Attribute('db', """database engine""")
    session = Attribute('session', """session class""")