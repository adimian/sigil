from collections import defaultdict
import logging

from flask import current_app as app
from ..api import db
from ldap3 import Server, Connection, ALL, SUBTREE, MODIFY_ADD, MODIFY_DELETE
from sqlalchemy import event

from ..models import User, VirtualGroup


logger = logging.getLogger(__name__)
LDAP_PERSON_CLASS = "extendedInetPerson"


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
        return self._search(search_base=search_base,
                            search_filter='(objectClass={})'.format(object_class),
                            attributes=attributes)

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

    def group_dn(self, group):
        return 'cn={},{}'.format(group.name,
                                 self.ou_dn(app.config['LDAP_GROUPS_OU']))

    def add_user(self, user):
        where = self.user_dn(user)
        self.connection.delete(where)
        # removing all empty values, as it displeases the LDAP gods
        ldap_dict = {key: value for (key, value) in user.ldap.items() if value}
        self.connection.add(where, LDAP_PERSON_CLASS, ldap_dict)
        self.check()

    def add_group(self, group):
        where = self.group_dn(group)
        self.connection.delete(where)
        attributes = {'uniqueMember': app.config['LDAP_BIND_DN']}
        self.connection.add(where, 'groupOfUniqueNames', attributes)

    def add_group_member(self, group, user):
        where = self.group_dn(group)
        what = {'uniqueMember': [(MODIFY_ADD, [self.user_dn(user)])]}
        self.connection.modify(where, what)
        self.check()

    def remove_group_member(self, group_dn, user_dn):
        what = {'uniqueMember': [(MODIFY_DELETE, [user_dn])]}
        self.connection.modify(group_dn, what)
        self.check()

    def _search(self, search_base, search_filter, attributes):
        ldap_search = self.connection.extend.standard.paged_search
        return ldap_search(search_base=search_base,
                           search_filter=search_filter,
                           attributes=attributes,
                           search_scope=SUBTREE,
                           paged_size=50,
                           generator=True)


def update_ldap():
    # create root groups
    con = LDAPConnection()
    con.add_ou(app.config['LDAP_GROUPS_OU'])
    con.add_ou(app.config['LDAP_USERS_OU'])

    # sync users
    db_users = set()
    ldap_users = set()

    logger.info('adding DB user to LDAP')
    for user in db.session.query(User).all():
        db_users.add(con.user_dn(user))
        con.add_user(user)

    logger.info('fetching LDAP users')
    for entry in con.search(con.ou_dn(app.config['LDAP_USERS_OU']),
                            object_class=LDAP_PERSON_CLASS):
        ldap_users.add(entry['dn'])

    logger.info('removing pruned users from LDAP')
    for removed_user in (ldap_users - db_users):
        logger.info('removing user "{}" from LDAP'.format(removed_user))
        con.delete(removed_user)

    # sync groups
    db_groups = set()
    db_group_members = defaultdict(set)
    ldap_groups = set()
    ldap_group_members = {}

    logger.info('adding DB virtual groups and their members to LDAP')
    for group in db.session.query(VirtualGroup).all():
        group_dn = con.group_dn(group)
        db_groups.add(group_dn)
        con.add_group(group)
        for user in group.members:
            db_group_members[group_dn].add(con.user_dn(user))
            con.add_group_member(group, user)
            logger.debug('adding {} to group {}'.format(user, group))

        for team in group.teams:
            for user in team.members:
                try:
                    db_group_members[group_dn].add(con.user_dn(user))
                    con.add_group_member(group, user)
                    logger.debug('adding {} to group {} '
                                 '(from team {})'.format(user, group, team))
                except LDAPError:
                    logger.warning('skipping addition of user {} '
                                   'to group {} (duplicate)'.format(user,
                                                                    group))

    logger.info('fetching LDAP groups and group members')
    for entry in con.search(con.ou_dn(app.config['LDAP_GROUPS_OU']),
                            object_class='groupOfUniqueNames',
                            attributes=['cn', 'uniqueMember']):
        group_dn = entry['dn']
        ldap_groups.add(group_dn)
        ldap_group_members[group_dn] = set(entry['attributes']['uniqueMember'])

    logger.info('removing members from LDAP groups')
    for group_dn in ldap_group_members:
        if group_dn not in db_groups:
            con.delete(group_dn)
        removed_members = (db_group_members[group_dn] -
                           ldap_group_members[group_dn])
        for removed_member in removed_members:
            logger.info('removing {} from group {}'.format(removed_member,
                                                           group_dn))
            con.remove_group_member(group_dn, removed_member)

    con.close()


def setup_auto_sync():
    @event.listens_for(db.session(), "after_transaction_end")
    def on_models_committed(session, transaction, *args):
        if session._model_changes:
            logger.info('Commencing ldap auto sync')
            update_ldap()
