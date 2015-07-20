# -*- coding: utf-8 -*-
from . import factory, proto, resource, service

__author__ = 'viruzzz-kun'


def make(config):
    return service.WsService(config)
