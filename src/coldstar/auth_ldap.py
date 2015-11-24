# -*- coding: utf-8 -*-

from coldstar.auth_mis import MisAuthObject
from coldstar.auth_mis import Person
from libcoldstar.plugin_helpers import ColdstarPlugin, Dependency
from twisted.internet import defer
from zope.interface import implementer
from libcastiel.exceptions import EInvalidCredentials
from libcastiel.interfaces import IAuthObject, IAuthenticator
from libcoldstar.twisted_helpers import deferred_to_thread

__author__ = 'viruzzz-kun'


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
class LdapAuthenticator(ColdstarPlugin):
    signal_name = 'libcoldstar.auth'
    db = Dependency('coldstar.db')

    @defer.inlineCallbacks
    def get_user(self, login, password):
        from twisted.internet import reactor
        from ldaptor.protocols.ldap import ldapconnector, ldapclient, ldapsyntax, ldaperrors

        if isinstance(login, unicode):
            login = login.encode('utf-8')
        if isinstance(password, unicode):
            password = password.encode('utf-8')

        server_ip = self.config.get('ldap_host', '127.0.0.1')
        server_port = self.config.get('ldap_port', 389)
        basedn = self.config.get('base_dn', 'OU=FNKC,DC=fccho-moscow,DC=ru')
        binddn, bindpw = login, password

        # query = '(sAMAccountName=%s)' % login
        c = ldapconnector.LDAPClientCreator(reactor, ldapclient.LDAPClient)
        overrides = {basedn: (server_ip, server_port)}
        client = yield c.connect(basedn, overrides=overrides)
        try:
            yield client.bind(binddn, bindpw)
        except ldaperrors.LDAPException as e:
            if e.name == 'invalidCredentials':
                raise EInvalidCredentials()
            raise
        result = yield self.get_user_int(login)
        defer.returnValue(result)
        # o = ldapsyntax.LDAPEntry(client, basedn)
        # results = yield o.search(filterText=query, sizeLimit=1)
        # if not results:
        #     raise EInvalidCredentials()
        # result = dict(
        #     (name, value[0])
        #     for name, value in results[0].items()
        # )
        # defer.returnValue(LdapAuthObject(result))

    @deferred_to_thread
    def get_user_int(self, login):
        if not self.db:
            raise Exception('Database is not initialized')
        with self.db.context_session(True) as session:
            result = session.query(Person).filter(Person.login == login).first()
            if result:
                return MisAuthObject(result)
            raise EInvalidCredentials


def make(config):
    return LdapAuthenticator(config)