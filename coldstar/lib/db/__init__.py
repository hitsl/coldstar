# -*- coding: utf-8 -*-
from . import interfaces, service
__author__ = 'mmalkov'


def make(config):
    return service.DataBaseService(config)