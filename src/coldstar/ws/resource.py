# -*- coding: utf-8 -*-
from autobahn.twisted.resource import WebSocketResource
from twisted.web.static import Data

from libcoldstar.web import AutoRedirectResource


__author__ = 'viruzzz-kun'


class WsTest(object):
    def echo(self, data):
        print(data)
        return data


def WsResource(ws_factory):
    ws_factory.bootstrap_test_functions()
    resource = AutoRedirectResource()
    resource.putChild('', WebSocketResource(ws_factory))
    resource.putChild('test', Data(test_page.encode('utf-8'), 'text/html; charset=utf-8'))
    return resource

test_page = u"""Here be test page"""