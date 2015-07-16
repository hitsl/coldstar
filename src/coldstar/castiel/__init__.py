#!/usr/bin/env python
# -*- coding: utf-8 -*-
from . import service
from coldstar.castiel import web, service

__author__ = 'viruzzz-kun'
__created__ = '08.02.2015'


def make(config):
    from libcoldstar.utils import safe_traverse
    s = service.CastielService()
    s.clean_period = safe_traverse(config, 'clean_period', default=10)
    s.expiry_time = safe_traverse(config, 'expiry_time', default=3600)
    return s