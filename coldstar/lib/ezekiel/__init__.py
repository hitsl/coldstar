#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'viruzzz-kun'
__created__ = '13.09.2014'

from . import service, rest


def make(config):
    return service.EzekielService(config)