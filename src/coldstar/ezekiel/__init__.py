#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'viruzzz-kun'
__created__ = '13.09.2014'

from . import service
from coldstar.ezekiel import rest, service


def make(config):
    return service.EzekielService(config)