# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from zope.interface import implementer
from .interfaces import IMisUserModel


Base = declarative_base()
metadata = Base.metadata

__author__ = 'mmalkov'


@implementer(IMisUserModel)
class Person(Base):
    __tablename__ = "Person"

    id = Column(Integer, primary_key=True, nullable=False)
    login = Column(String, index=True, nullable=False)
    password = Column(String, nullable=False)