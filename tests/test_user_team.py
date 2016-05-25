import json

from sigil.models import UserTeam, User


def test_create_team(client):
    rv = client.post('/team',
                     data={'name': 'sysadmins'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)
    assert UserTeam.query.filter_by(name='sysadmins').one()


def test_create_too_many_teams(client):
    rv = client.post('/team',
                     data={'name': 'sysadmins'},
                     headers=client._auth_headers)
    assert rv.status_code == 200

    rv = client.post('/team',
                     data={'name': 'sysadmins'},
                     headers=client._auth_headers)
    assert rv.status_code == 409


def test_disable_team(client):
    rv = client.post('/team',
                     data={'name': 'sysadmins'},
                     headers=client._auth_headers)
    assert rv.status_code == 200

    rv = client.patch('/team',
                      data={'name': 'sysadmins',
                            'active': False},
                      headers=client._auth_headers)
    assert rv.status_code == 200
    assert UserTeam.by_name('sysadmins').active is False


def test_add_members(client):
    rv = client.post('/team',
                     data={'name': 'sysadmins'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.post('/team/members',
                     data={'name': 'sysadmins',
                           'usernames': json.dumps(['alice', 'bernard'])},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    user = client._db.session.query(User).filter_by(username='alice').one()
    assert [g.name for g in user.teams] == ['sysadmins']

    rv = client.get('/user/details',
                    headers=client._auth_headers)

    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['teams'] == ['sysadmins']


def test_add_too_many_members(client):
    rv = client.post('/team',
                     data={'name': 'sysadmins'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.post('/team/members',
                     data={'name': 'sysadmins',
                           'usernames': json.dumps(['alice', 'bernard'])},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.post('/team/members',
                     data={'name': 'sysadmins',
                           'usernames': json.dumps(['alice'])},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    group = client._db.session.query(UserTeam).filter_by(name='sysadmins').one()
    assert [m.username for m in group.members] == ['alice', 'bernard']


def test_get_members(client):
    rv = client.post('/team',
                     data={'name': 'sysadmins'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.post('/team/members',
                     data={'name': 'sysadmins',
                           'usernames': json.dumps(['alice', 'bernard'])},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.get('/team/members',
                    data={'name': 'sysadmins'},
                    headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)
    data = json.loads(rv.data.decode('utf-8'))
    assert sorted([u['username'] for u in data['users']]) == sorted(['alice',
                                                                     'bernard'])


def test_add_non_members(client):
    rv = client.post('/team',
                     data={'name': 'sysadmins'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.post('/team/members',
                     data={'name': 'sysadmins',
                           'usernames': json.dumps(['alice', 'bernard',
                                                    'charlie'])},
                     headers=client._auth_headers)
    assert rv.status_code == 404, str(rv.data)


def test_add_bad_group(client):
    rv = client.post('/team',
                     data={'name': 'sysadmins'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.post('/team/members',
                     data={'name': 'postgres',
                           'usernames': json.dumps(['alice', 'bernard'])},
                     headers=client._auth_headers)
    assert rv.status_code == 404, str(rv.data)


def test_group_remove_members(client):
    rv = client.post('/team',
                     data={'name': 'sysadmins'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.post('/team/members',
                     data={'name': 'sysadmins',
                           'usernames': json.dumps(['alice', 'bernard'])},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.delete('/team/members',
                       data={'name': 'sysadmins',
                             'usernames': json.dumps(['alice'])},
                       headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    session = client._db.session
    group = session.query(UserTeam).filter_by(name='sysadmins').one()
    assert [m.username for m in group.members] == ['bernard']


# permissions
def test_set_permissions(client):
    rv = client.post('/app/register', data={'name': 'newapp'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.post('/team',
                     data={'name': 'sysadmins'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.post('/team/permissions',
                     data={'context': 'newapp',
                           'name': 'sysadmins',
                           'needs': json.dumps([['permissions', 'read']])},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)
    data = json.loads(rv.data.decode('utf-8'))
    assert sorted(data['provides']) == sorted([['permissions', 'read']])


def test_delete_permissions(client):
    rv = client.post('/app/register', data={'name': 'newapp'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.post('/team',
                     data={'name': 'sysadmins'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.post('/team/permissions',
                     data={'context': 'newapp',
                           'name': 'sysadmins',
                           'needs': json.dumps([['permissions', 'read'],
                                                ['permissions', 'write']])},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)
    data = json.loads(rv.data.decode('utf-8'))
    assert sorted(data['provides']) == sorted([['permissions', 'read'],
                                               ['permissions', 'write']])

    rv = client.delete('/team/permissions',
                       data={'context': 'newapp',
                             'name': 'sysadmins',
                             'needs': json.dumps([['permissions', 'write']])},
                       headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)
    data = json.loads(rv.data.decode('utf-8'))
    assert sorted(data['provides']) == sorted([['permissions', 'read']])


def test_get_permissions(client):
    rv = client.post('/app/register', data={'name': 'newapp'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.post('/team',
                     data={'name': 'sysadmins'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.post('/team/permissions',
                     data={'context': 'newapp',
                           'name': 'sysadmins',
                           'needs': json.dumps([['permissions', 'read']])},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.get('/team/permissions',
                    data={'context': 'newapp',
                          'name': 'sysadmins'},
                    headers=client._auth_headers)

    assert rv.status_code == 200, str(rv.data)
    data = json.loads(rv.data.decode('utf-8'))
    assert sorted(data['provides']) == sorted([['permissions', 'read'], ])
