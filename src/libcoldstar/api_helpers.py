# -*- coding: utf-8 -*-
import json
from libcoldstar.utils import as_json
from twisted.internet import reactor
from twisted.python.compat import nativeString
from twisted.web.client import URI, HTTPClientFactory

__author__ = 'viruzzz-kun'


def _json_loads(data):
    try:
        return json.loads(data)
    except ValueError:
        return None


def get_json(url, *args, **kwargs):
    """
    :param json: JSON data
    :param url:
    :param args:
    :param kwargs:
    :return:
    """
    j = kwargs.pop('json', None)
    if j:
        kwargs['postdata'] = as_json(j)
    kwargs.setdefault('agent', 'Twisted JSON Adapter')
    uri = URI.fromBytes(url)
    factory = HTTPClientFactory(url, *args, **kwargs)
    factory.noisy = 0
    if uri.scheme == b'https':
        from twisted.internet import ssl
        contextFactory = ssl.ClientContextFactory()
        reactor.connectSSL(
            nativeString(uri.host), uri.port, factory, contextFactory)
    else:
        reactor.connectTCP(nativeString(uri.host), uri.port, factory)
    return factory.deferred.addCallback(_json_loads)
