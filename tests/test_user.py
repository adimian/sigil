import json


def test_get_details(client):
    rv = client.get('/user/details',
                    headers=client._auth_headers)

    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['username'] == client._user.username


def test_get_permissions(client):
    rv = client.get('/user/permissions',
                    data={'context': 'sigil'},
                    headers=client._auth_headers)

    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['provides'] == [['teams', 'read'],
                                ['teams', 'write'],
                                ['users', 'read'],
                                ['users', 'write'],
                                ['appcontexts', 'read'],
                                ['appcontexts', 'write']]
