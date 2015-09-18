import json

from sigil.models import User


def test_get_details(client):
    rv = client.get('/user/details',
                    headers=client._auth_headers)

    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['username'] == client._user.username


def test_set_details(client):
    rv = client.post('/user/details', data={'firstname': 'bob'},
                     headers=client._auth_headers)

    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    user = User.query.get(data['id'])
    assert user.firstname == 'bob'


def test_set_protected_details(client):
    rv = client.post('/user/details', data={'api_key': 'new_key'},
                     headers=client._auth_headers)

    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    user = User.query.get(data['id'])
    assert user.api_key != 'new_key'


def test_get_catalog(client):
    rv = client.get('/user',
                    data={'context': 'sigil'},
                    headers=client._auth_headers)

    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert sorted([u['username'] for u in data['users']]) == sorted(['alice',
                                                                     'bernard'])


def test_search_user(client):
    rv = client.get('/user/search',
                    data={'query': 'lice',
                          'context': 'sigil'},
                    headers=client._auth_headers)
    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['users'][0]['username'] == 'alice'
    assert len(data['users']) == 1


def test_get_permissions(client):
    rv = client.get('/user/permissions',
                    data={'context': 'sigil'},
                    headers=client._auth_headers)

    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert sorted(data['provides']) == sorted([['teams', 'read'],
                                               ['teams', 'write'],
                                               ['users', 'read'],
                                               ['users', 'write'],
                                               ['groups', 'read'],
                                               ['groups', 'write'],
                                               ['appcontexts', 'read'],
                                               ['appcontexts', 'write']])


def test_get_permissions_catalog(client):
    rv = client.options('/user/permissions',
                        headers=client._auth_headers)

    assert rv.status_code == 200, str(rv.data)
    data = json.loads(rv.data.decode('utf-8'))
    assert set(data.keys()) == set(['sigil'])
    assert sorted(data['sigil']) == sorted([[['teams', 'read'], True],
                                            [['teams', 'write'], True],
                                            [['users', 'read'], True],
                                            [['users', 'write'], True],
                                            [['groups', 'read'], True],
                                            [['groups', 'write'], True],
                                            [['appcontexts', 'read'], True],
                                            [['appcontexts', 'write'], True]])


def test_set_permissions(client):
    rv = client.post('/app/register', data={'name': 'newapp'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.post('/user/permissions',
                     data={'context': 'newapp',
                           'username': 'bernard',
                           'needs': json.dumps([['permissions', 'read']])},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)
    data = json.loads(rv.data.decode('utf-8'))
    assert sorted(data['provides']) == sorted([['permissions', 'read']])


def test_delete_permissions(client):
    rv = client.post('/app/register', data={'name': 'newapp'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.post('/user/permissions',
                     data={'context': 'newapp',
                           'username': 'bernard',
                           'needs': json.dumps([['permissions', 'read'],
                                                ['permissions', 'write']])},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)
    data = json.loads(rv.data.decode('utf-8'))
    assert sorted(data['provides']) == sorted([['permissions', 'read'],
                                               ['permissions', 'write']])

    rv = client.delete('/user/permissions',
                       data={'context': 'newapp',
                             'username': 'bernard',
                             'needs': json.dumps([['permissions', 'write']])},
                       headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)
    data = json.loads(rv.data.decode('utf-8'))
    assert sorted(data['provides']) == sorted([['permissions', 'read']])


def test_get_api_key(client):
    rv = client.get('/user/key', headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)
    data = json.loads(rv.data.decode('utf-8'))
    assert data['key'] == User.query.get(client._user.id).api_key


def test_reset_api_key(client):
    rv = client.get('/user/key', headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)
    data = json.loads(rv.data.decode('utf-8'))
    key1 = data['key']
    rv = client.post('/user/key', headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)
    data = json.loads(rv.data.decode('utf-8'))
    assert data['key']

    rv = client.get('/user/key', headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)
    data = json.loads(rv.data.decode('utf-8'))
    assert data['key'] != key1
    assert data['key'] == User.query.get(client._user.id).api_key


def test_change_password(client):
    rv = client.post('/user/password', data={'old_password': 'test',
                                             'new_password': 'hello'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)
    assert User.query.get(client._user.id).is_correct_password('hello')
