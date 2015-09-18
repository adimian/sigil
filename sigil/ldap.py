import logging

from flask import current_app as app
from ldap3 import Server, Connection, ALL, SUBTREE

from .api import db
from .models import User


logger = logging.getLogger(__name__)


class LDAPError(Exception):
    pass


class LDAPConnection(object):
    def __init__(self):
        self._connection = None

    def _connect(self):
        server = Server(app.config['LDAP_HOST'], get_info=ALL)
        conn = Connection(server, user=app.config['LDAP_BIND_DN'],
                          password=app.config['LDAP_BIND_PASSWORD'])
        logger.info(conn)
        logger.info('ldap connected: {}'.format(conn.bind()))
        return conn

    def close(self):
        self.connection.unbind()

    def search(self, search_base, object_class, attributes=['cn']):
        ldap_search = self.connection.extend.standard.paged_search
        return ldap_search(search_base=search_base,
                           search_filter='(objectClass={})'.format(object_class),
                           search_scope=SUBTREE,
                           attributes=attributes,
                           paged_size=50,
                           generator=True)

    @property
    def connection(self):
        if not self._connection:
            self._connection = self._connect()
        return self._connection

    @property
    def root(self):
        return app.config['LDAP_ROOT_DN']

    @property
    def result(self):
        return self.connection.result

    def delete(self, dn):
        self.connection.delete(dn)

    def add_ou(self, name):
        where = self.ou_dn(name)
        self.connection.add(where, 'organizationalUnit')

    def check(self):
        if int(self.result['result']):
            raise LDAPError('Code: {} = {}'.format(self.result['result'],
                                                   self.result['message']))

    def user_dn(self, user):
        return 'cn={},{}'.format(user.username,
                                 self.ou_dn(app.config['LDAP_USERS_OU']))

    def ou_dn(self, name):
        if self.root not in name:
            name = 'ou={},{}'.format(name, self.root)
        return name

    def add_user(self, user):
        where = self.user_dn(user)
        self.connection.delete(where)

        self.connection.add(where, 'inetOrgPerson', user.ldap)
        self.check()


def update_ldap():
    # create root groups
    con = LDAPConnection()
    con.add_ou(app.config['LDAP_GROUPS_OU'])
    con.add_ou(app.config['LDAP_USERS_OU'])

    # sync users
    db_users = set()
    ldap_users = set()

    for user in db.session.query(User).all():
        db_users.add(con.user_dn(user))
        con.add_user(user)

    for entry in con.search(con.ou_dn(app.config['LDAP_USERS_OU']),
                            object_class='inetOrgPerson'):
        ldap_users.add(entry['dn'])

    for removed_user in (ldap_users - db_users):
        logger.info('removing user "{}" from LDAP'.format(removed_user))
        con.delete(removed_user)

    con.close()
