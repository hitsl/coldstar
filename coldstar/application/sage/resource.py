# -*- coding: utf-8 -*-
from twisted.internet import defer
from twisted.python.components import registerAdapter
from twisted.web.error import UnsupportedMethod
from zope.interface import implementer
from twisted.web.resource import Resource, IResource
from coldstar.application.sage.interfaces import ISettingsService

from coldstar.lib.utils import api_method


__author__ = 'viruzzz-kun'

@implementer(IResource)
class SettingsResource(Resource):
    isLeaf = True
    db = None

    def __init__(self, service):
        self.service = service
        Resource.__init__(self)

    @api_method
    @defer.inlineCallbacks
    def render(self, request):
        request.setHeader('content-type', 'application/json; charset=utf-8')
        ppl = len(request.postpath)
        if ppl == 1:
            if request.method == 'GET':
                result = yield self.service.get_value(request.postpath[0], subtree=('subtree' in request.args))
            elif request.method == 'POST':
                result = yield self.service.set_value(request.postpath[0], request.content)
            else:
                raise UnsupportedMethod(['GET', 'POST'])
        else:
            result = 'Settings service'
        defer.returnValue(result)


registerAdapter(SettingsResource, ISettingsService, IResource)