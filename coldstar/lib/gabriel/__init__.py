# -*- coding: utf-8 -*-
from . import service, web

__author__ = 'viruzzz-kun'


def make(config):
    return service.GabrielService(config)