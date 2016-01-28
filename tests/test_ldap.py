import json
from unittest.mock import call

from sigil.ldap import setup_auto_sync, update_ldap


def test_update_ldap_user(client, mocker):
    setup_auto_sync()

    connect = mocker.patch('sigil.ldap.LDAPConnection._connect')
    mocker.patch('sigil.ldap.LDAPConnection.check')

    rv = client.post('/user/details', data={'firstname': 'bob'},
                     headers=client._auth_headers)

    assert rv.status_code == 200

    add = connect().add
    add.assert_has_calls((call('ou=Groups,dc=mycorp,dc=com',
                               'organizationalUnit'),
                          call('ou=Users,dc=mycorp,dc=com',
                               'organizationalUnit')))


def test_update_ldap_group(client, mocker):

    rv = client.post('/group',
                     data={'name': 'jabber'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    setup_auto_sync()

    connect = mocker.patch('sigil.ldap.LDAPConnection._connect')
    mocker.patch('sigil.ldap.LDAPConnection.check')

    rv = client.post('/group/members',
                     data={'name': 'jabber',
                           'usernames': json.dumps(['alice', 'bernard'])},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    add = connect().add
    modify = connect().modify

    add.assert_has_calls([call('cn=jabber,ou=Groups,dc=mycorp,dc=com',
                               'groupOfUniqueNames',
                               {'uniqueMember':
                                'cn=admin,dc=mycorp,dc=com'})])

    modify.assert_has_calls((call('cn=jabber,ou=Groups,dc=mycorp,dc=com',
                                  {'uniqueMember': [('MODIFY_ADD',
                                                     ['cn=alice,ou=Users,dc=mycorp,dc=com'])]}),
                             call('cn=jabber,ou=Groups,dc=mycorp,dc=com',
                                  {'uniqueMember': [('MODIFY_ADD',
                                                     ['cn=bernard,ou=Users,dc=mycorp,dc=com'])]})),
                            any_order=True)


def test_update_ldap_group_remove_users(client, mocker):
    ''' need to manually call update_ldap() because of how sqlalchemy is tied
    to the session, the automatic ldap updates only occurs once per session
    which occurs properly when dealing with tornado-based requests, but not
    the flask test client
    '''
    with client._app.app_context():

        # create group

        rv = client.post('/group',
                         data={'name': 'jabber'},
                         headers=client._auth_headers)
        assert rv.status_code == 200, str(rv.data)

        # add members
        rv = client.post('/group/members',
                         data={'name': 'jabber',
                               'usernames': json.dumps(['alice', 'bernard'])},
                         headers=client._auth_headers)
        assert rv.status_code == 200, str(rv.data)

        mocker.patch('sigil.ldap.LDAPConnection._connect')
        mocker.patch('sigil.ldap.LDAPConnection.check')
        update_ldap()

        # remove one member

        rv = client.delete('/group/members',
                           data={'name': 'jabber',
                                 'usernames': json.dumps(['alice'])},
                           headers=client._auth_headers)
        assert rv.status_code == 200, str(rv.data)

        connect = mocker.patch('sigil.ldap.LDAPConnection._connect')
        mocker.patch('sigil.ldap.LDAPConnection.check')
        update_ldap()

        modify = connect().modify

        assert modify.mock_calls.count(call('cn=jabber,ou=Groups,dc=mycorp,dc=com',
                                            {'uniqueMember': [('MODIFY_ADD',
                                                               ['cn=bernard,ou=Users,dc=mycorp,dc=com'])]})) == 1

        assert modify.mock_calls.count(call('cn=jabber,ou=Groups,dc=mycorp,dc=com',
                                            {'uniqueMember': [('MODIFY_ADD',
                                                               ['cn=alice,ou=Users,dc=mycorp,dc=com'])]})) == 0

