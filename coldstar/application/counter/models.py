# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, Date, Unicode
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


__author__ = 'viruzzz-kun'

Base = declarative_base()
metadata = Base.metadata


class rbCounter(Base):
    __tablename__ = "rbCounter"

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


class ClientIdentification(Base):
    __tablename__ = u'ClientIdentification'
    __table_args__ = (
        Index(u'accountingSystem_id', u'accountingSystem_id', u'identifier'),
    )

    id = Column(Integer, primary_key=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    client_id = Column(ForeignKey('Client.id'), nullable=False, index=True)
    accountingSystem_id = Column(Integer, ForeignKey('rbAccountingSystem.id'), nullable=False)
    identifier = Column(String(16), nullable=False)
    checkDate = Column(Date)

    accountingSystems = relationship(u'rbAccountingSystem', lazy=False)


class rbAccountingSystem(Base):
    __tablename__ = u'rbAccountingSystem'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)
    isEditable = Column(Integer, nullable=False, server_default=u"'0'")
    showInClientInfo = Column(Integer, nullable=False, server_default=u"'0'")