# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base


__author__ = 'viruzzz-kun'

Base = declarative_base()
metadata = Base.metadata


class Settings(Base):
    __tablename__ = "Setting"

    id = Column(Integer, primary_key=True, nullable=False)
    path = Column(String, index=True, unique=True, nullable=False)
    value = Column(String, nullable=False)
