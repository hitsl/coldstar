#!/usr/bin/env python
# -*- coding: utf-8 -*-
from . import interfaces, service, web

__author__ = 'viruzzz-kun'
__created__ = '08.02.2015'


def make(config):
    from coldstar.lib.utils import safe_traverse
    s = service.CastielService()
    s.clean_period = safe_traverse(config, 'clean_period', default=10)
    s.cookie_name = safe_traverse(config, 'cookie_name', default='CastielAuthToken')
    s.expiry_time = safe_traverse(config, 'expiry_time', default=3600)
    s.cors_domain = safe_traverse(config, 'cors_domain', default='http://127.0.0.1:5001')
    s.cookie_domain = safe_traverse(config, 'cookie_domain', default='127.0.0.1')
    return s