# -*- coding: utf-8 -*-
from . import interfaces, service, web, session

__author__ = 'viruzzz-kun'


def make(config):
    return service.GabrielService(config)