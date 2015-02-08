#!/usr/bin/env python
# -*- coding: utf-8 -*-
from twisted.python.components import registerAdapter
from twisted.web.resource import IResource, Resource
from twisted.web.static import Data

from zope.interface import implementer
from coldstar.lib.castiel.interfaces import ICasService
from coldstar.lib.castiel.rpc import CastielApiResource
from coldstar.lib.castiel.user_login import CastielLoginResource


__author__ = 'viruzzz-kun'
__created__ = '08.02.2015'


@implementer(IResource)
class CastielWebResource(Resource):
    def __init__(self, castiel_service):
        Resource.__init__(self)
        self.service = castiel_service
        self.api = CastielApiResource(castiel_service)
        self.login = CastielLoginResource(castiel_service)
        self.putChild('api', self.api)
        self.putChild('login', self.login)
        self.putChild('', Data('I am Castiel, angel of God', 'text/html'))


registerAdapter(CastielWebResource, ICasService, IResource)