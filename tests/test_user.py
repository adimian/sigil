import json


def test_get_details(client):
    rv = client.get('/user/details',
                    headers=client._auth_headers)

    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['username'] == client._user.username


def test_get_catalog(client):
    rv = client.get('/user',
                    data={'context': 'sigil'},
                    headers=client._auth_headers)

    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data == {'users':
                    [{'display_name': 'alice alice',
                      'id': 1,
                      'username': 'alice'},
                     {'display_name': 'bernard bernard',
                      'id': 2,
                      'username': 'bernard'}]}


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
                                               ['appcontexts', 'read'],
                                               ['appcontexts', 'write']])


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
