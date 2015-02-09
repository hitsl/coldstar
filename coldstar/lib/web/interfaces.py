#!/usr/bin/env python
# -*- coding: utf-8 -*-
from zope.interface import Interface, Attribute

__author__ = 'viruzzz-kun'
__created__ = '08.02.2015'


class ITemplatedRequest(Interface):
    currentAppPath = Attribute('currentAppPath', 'Current Application Path')

    def render_template(self, name, **kwargs):
        """
        Render template by name
        :param name:
        :param kwargs:
        :return:
        """

    def rememberAppPath(self):
        """
        Set currentAppPath
        """

class IWebSession(Interface):
    flashed_messages = Attribute('Flashed Messages')
    back = Attribute('Where to return after login success')

    def get_flashed_messages(self):
        pass

    def flash_message(self, message):
        pass


class ITemplatedSite(Interface):
    jinja_env = Attribute('jinja_env', 'Jinja Environment')