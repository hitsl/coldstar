#!/usr/bin/env python
# -*- coding: utf-8 -*-
from zope.interface import Interface, Attribute

__author__ = 'viruzzz-kun'
__created__ = '08.02.2015'


class IAuthenticator(Interface):
    db = Attribute('db', 'Database Service')

    def get_user(self, login, password):
        """
        Get authentication object
        :param login: user login
        :param password: user password
        :return: Deferred which fires either object or failure
        """


class IAuthObject(Interface):
    user_id = Attribute('user_id', 'User unique id')
    login = Attribute('login', 'User login')