#!/usr/bin/env python
# -*- coding: utf-8 -*-
from . import interfaces, wrappers, service

__author__ = 'viruzzz-kun'
__created__ = '08.02.2015'


def make(config):
    return service.WebService(config)