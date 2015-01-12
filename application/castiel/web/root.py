# -*- coding: utf-8 -*-
from twisted.python.components import registerAdapter
from twisted.web.resource import IResource, Resource
from twisted.web.static import Data
from zope.interface import implementer

from ..interfaces import ICasService
from lib.excs import SerializableBaseException


__author__ = 'viruzzz-kun'


class ENoToken(SerializableBaseException):
    def __init__(self):
        self.message = 'Token cookie is not set'


class CastielResourceMixin:
    cookie_name = 'CastielAuthToken'

    def _get_hex_token(self, request):
        token = request.getCookie(self.cookie_name)
        if token:
            print(token)
            return token.decode('hex')
        raise ENoToken()


@implementer(IResource)
class CastielWebResource(Resource, CastielResourceMixin):
    def __init__(self, castiel_service):
        Resource.__init__(self)
        from application.castiel.web.rest import CastielApiResource
        from application.castiel.web.ui import CastielUserResource
        self.service = castiel_service
        self.api = CastielApiResource(castiel_service)
        self.user = CastielUserResource(castiel_service)
        self.putChild('api', self.api)
        self.putChild('user', self.user)
        self.putChild('', Data('I am Castiel, angel of God', 'text/html'))

registerAdapter(CastielWebResource, ICasService, IResource)