# -*- coding: utf-8 -*-
from coldstar.db import interfaces, service
from coldstar.db import service

__author__ = 'mmalkov'


def make(config):
    return service.DataBaseService(config)