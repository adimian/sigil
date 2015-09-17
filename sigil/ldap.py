import logging

from flask import current_app as app
from ldap3 import Server, Connection, ALL

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

    def add_group(self, where):
        if self.root not in where:
            where = '{},{}'.format(where, self.root)
        self.connection.add(where, 'organizationalUnit')

    def check(self):
        if int(self.result['result']):
            raise LDAPError('Code: {} = {}'.format(self.result['result'],
                                                   self.result['message']))

    def add_user(self, user):
        where = 'cn={},{},{}'.format(user.username,
                                     app.config['LDAP_USERS_OU'],
                                     self.root)
        self.connection.delete(where)

        data = {'surname': user.surname,
                'uid': user.username,
                'givenName': user.firstname,
                'displayName': user.display_name,
                'mail': user.email}
        if user.password:
            data['userPassword'] = user.password
        if user.mobile_number:
            data['mobile'] = user.mobile_number
        self.connection.add(where, 'inetOrgPerson', data)
        self.check()


def update_ldap():
    # create root groups
    con = LDAPConnection()
    con.add_group(app.config['LDAP_GROUPS_OU'])
    con.add_group(app.config['LDAP_USERS_OU'])

    for user in db.session.query(User).all():
        con.add_user(user)
    con.close()
