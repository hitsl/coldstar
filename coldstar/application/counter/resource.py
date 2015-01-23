# -*- coding: utf-8 -*-
from twisted.python.components import registerAdapter
from twisted.web.resource import Resource, IResource
from zope.interface import implementer

from .interfaces import ICounterService
from coldstar.lib.excs import BadRequest
from coldstar.lib.utils import api_method


__author__ = 'viruzzz-kun'


@implementer(IResource)
class CounterResource(Resource):
    isLeaf = True
    service = None

    def __init__(self, service):
        Resource.__init__(self)
        self.service = service

    @api_method
    def render(self, request):
        request.setHeader('content-type', 'application/json; charset=utf-8')
        ppl = len(request.postpath)

        if ppl == 1:
            if request.postpath[0] == 'acquire':
                if 'counter_id' not in request.args:
                    raise BadRequest
                counter_id = int(request.args['counter_id'][0])
                client_id = None
                if 'client_id' in request.args:
                    client_id = int(request.args['client_id'][0])
                return self.service.acquire(counter_id, client_id)

registerAdapter(CounterResource, ICounterService, IResource)