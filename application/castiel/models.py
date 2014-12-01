# -*- coding: utf-8 -*-
from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata

__author__ = 'mmalkov'


class Person(Base):
    __tablename__ = "Person"

    id = Column(Integer, primary_key=True, nullable=False)
    login = Column(String, index=True, nullable=False)
    password = Column(String, nullable=False)