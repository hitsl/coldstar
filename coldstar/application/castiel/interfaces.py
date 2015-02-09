#!/usr/bin/env python
# -*- coding: utf-8 -*-
from zope.interface import Interface, Attribute

__author__ = 'viruzzz-kun'
__created__ = '08.02.2015'


class IMisUserModel(Interface):
    id = Attribute('id', 'Person.id')
    login = Attribute('login', 'Person.login')
    password = Attribute('password', 'Person.password, md5 hash')