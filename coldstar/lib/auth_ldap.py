# -*- coding: utf-8 -*-
import blinker
from ldaptor.protocols.ldap.ldaperrors import LDAPException
from twisted.internet import defer
from zope.interface import implementer
from coldstar.lib.castiel.exceptions import EInvalidCredentials
from coldstar.lib.castiel.interfaces import IAuthObject
from coldstar.lib.castiel.interfaces import IAuthenticator

__author__ = 'viruzzz-kun'

boot = blinker.signal('coldstar:boot')
self_boot = blinker.signal('coldstar.lib.auth:boot')


@implementer(IAuthObject)
class LdapAuthObject(object):
    __slots__ = ['user_id', 'login', 'groups']
    msgpack = 1

    def __init__(self, entry=None):
        if entry:
            self.user_id = None  # entry['objectGUID'].encode('base64')
            self.login = entry['sAMAccountName']
        else:
            self.user_id = None
            self.login = None
        self.groups = []

    def __getstate__(self):
        return [
            self.user_id,
            self.login,
            self.groups,
            ]

    def __setstate__(self, state):
        self.user_id, self.login, self.groups = state


@implementer(IAuthenticator)
class LdapAuthenticator(object):
    def __init__(self, config):
        self.config = config
        boot.connect(self.bootstrap_mis_auth)

    def bootstrap_mis_auth(self, _):
        print('Auth Ldap: initialized')
        self_boot.send(self)

    @defer.inlineCallbacks
    def get_user(self, login, password):
        from twisted.internet import reactor
        from ldaptor.protocols.ldap import ldapconnector, ldapclient, ldapsyntax

        if isinstance(login, unicode):
            login = login.encode('utf-8')
        if isinstance(password, unicode):
            password = password.encode('utf-8')

        server_ip = self.config.get('ldap_host', '127.0.0.1')
        server_port = self.config.get('ldap_port', 389)
        basedn = self.config.get('base_dn', 'OU=FNKC,DC=fccho-moscow,DC=ru')
        binddn, bindpw = login, password

        query = '(sAMAccountName=%s)' % login
        c = ldapconnector.LDAPClientCreator(reactor, ldapclient.LDAPClient)
        overrides = {basedn: (server_ip, server_port)}
        client = yield c.connect(basedn, overrides=overrides)
        try:
            yield client.bind(binddn, bindpw)
        except LDAPException as e:
            if e.name == 'invalidCredentials':
                raise EInvalidCredentials()
            raise
        o = ldapsyntax.LDAPEntry(client, basedn)
        results = yield o.search(filterText=query, sizeLimit=1)
        if not results:
            raise EInvalidCredentials()
        result = dict(
            (name, value[0])
            for name, value in results[0].items()
        )
        defer.returnValue(LdapAuthObject(result))


def make(config):
    return LdapAuthenticator(config)