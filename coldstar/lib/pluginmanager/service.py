#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ConfigParser import ConfigParser
import blinker
import os
from twisted.application.service import MultiService
from coldstar.lib.utils import safe_int

__author__ = 'viruzzz-kun'
__created__ = '04.04.2015'


boot = blinker.signal('coldstar:boot')


def set_value(d, path, items):
    if not path:
        raise Exception('WTF')
    while len(path) > 1:
        key, path = path[0], path[1:]
        if key not in d:
            d[key] = {}
        d = d[key]
    key = path[0]
    if key not in d:
        d[key] = {}
    d[key].update((k, safe_int(v)) for k, v in items)
    return


def parse_config(fp):
    cp = ConfigParser()
    cp.readfp(fp)
    result = {}
    for section in cp.sections():
        path = section.split(':')
        set_value(result, path, cp.items(section))
    return result


def make_config(filename=None):
    config = {}
    try:
        with open('default.conf') as cfg_file:
            config.update(parse_config(cfg_file))
    except (IOError, OSError):
        print(u'CAUTION! Cannot load default config!')
        print(u'Current directory = %s' % os.getcwdu())

    if filename:
        try:
            with open(filename, 'rt') as cfg_file:
                config.update(parse_config(cfg_file))
        except (IOError, OSError):
            print(u'Cannot load file: %s' % filename)
            print(u'Cannot load config. Using defaults.')
    return config


def make_plugin(name, config):
    module = __import__(name, globals(), locals(), ['make'])
    if not hasattr(module, 'make'):
        print('Module "%s" has no attribute "make"' % name)
        return None
    return module.make(config)


class Application(MultiService):
    def __init__(self, options):
        MultiService.__init__(self)
        self.options = options
        self.plugins = {}
        self.config = {}
        self.modules = []
        self.reload_config()

    def reload_config(self):
        import pprint
        config = self.config = make_config(self.options['config'])
        pprint.pprint(config)
        self.modules = []
        for name, cfg in config.get('module', {}).iteritems():
            print('Loading plugin: %s' % name)
            self.modules.append(make_plugin(name, cfg))

    def startService(self):
        from twisted.python.log import callWithContext
        print('...Booting...')
        callWithContext({"system": "Bootstrap"}, boot.send, self)
        MultiService.startService(self)

