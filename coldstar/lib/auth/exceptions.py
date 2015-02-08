#!/usr/bin/env python
# -*- coding: utf-8 -*-
from coldstar.lib.excs import SerializableBaseException

__author__ = 'viruzzz-kun'
__created__ = '08.02.2015'


class EInvalidCredentials(SerializableBaseException):
    def __init__(self):
        self.message = 'Incorrect login or password'


