# -*- coding: utf-8 -*-
import json

from libcoldstar.api_helpers import get_json
from libcoldstar.plugin_helpers import ColdstarPlugin
from libcoldstar.utils import as_json
from twisted.internet import defer
from libcastiel.exceptions import EInvalidCredentials, EExpiredToken
from libcastiel.objects import AuthTokenObject

__author__ = 'viruzzz-kun'


class RemoteCas(ColdstarPlugin):
    signal_name = 'coldstar.castiel'

    def __init__(self, config):
        self.cas_url = config.get('url', 'http://127.0.0.1/').rstrip('/') + '/cas/api/'

    def acquire_token(self, login, password):
        def _cb(j):
            if j['success']:
                return AuthTokenObject(j['user'], j['deadline'], j['token'])
            exception = j['exception']
            if exception == 'EInvalidCredentials':
                raise EInvalidCredentials
            raise Exception(j)

        return get_json(
            self.cas_url + 'acquire',
            postdata=as_json({'login': login, 'password': password})
        ).addCallback(_cb)

    def release_token(self, token):
        def _cb(j):
            if j['success']:
                return True
            return defer.fail(EExpiredToken(token))

        return get_json(
            self.cas_url + 'release',
            postdata=as_json({'token': token})
        ).addCallback(_cb)

    def check_token(self, token, prolong=False):
        def _cb(j):
            if j['success']:
                return j['user_id'], j['deadline']
            return defer.fail(EExpiredToken(token))

        send = {'token': token}
        if prolong:
            send['prolong'] = True

        return get_json(
            self.cas_url + 'check', postdata=as_json(send)
        ).addCallback(_cb)

    def prolong_token(self, token):
        def _cb(j):
            if j['success']:
                return True, j['deadline']
            return defer.fail(EExpiredToken(token))
        return get_json(
            self.cas_url + 'prolong',
            postdata=as_json({'token': token})
        ).addCallback(_cb)


def make(config):
    return RemoteCas(config)
