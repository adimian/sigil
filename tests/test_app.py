import json


def register_app(client):
    rv = client.post('/app/register', data={'name': 'newapp'},
                     headers=client._auth_headers)
    data = json.loads(rv.data.decode('utf-8'))
    assert rv.status_code == 200, 'unable to register app'
    return data['application-key']


def test_register_app(client):
    register_app(client)


def test_list_apps(client):
    register_app(client)
    rv = client.get('/app', headers=client._auth_headers)
    data = json.loads(rv.data.decode('utf-8'))
    assert data['apps'][-1] == {'id': 2, 'name': 'newapp'}


def test_expose_needs(client):
    app_key = register_app(client)

    needs = (('objects', 'write'),
             ('objects', 'read'),
             ('objects', 'read'),
             ('objects', 'execute'))

    rv = client.post('/needs', data={'needs': json.dumps(needs),
                                     'application-key': app_key})

    assert rv.status_code == 200, str(rv.data)

    data = json.loads(rv.data.decode('utf-8'))
    assert set(map(tuple, data['needs'])).issuperset(set(needs))


def test_delete_needs(client):
    app_key = register_app(client)

    needs = (('objects', 'write'),
             ('objects', 'read'),
             ('objects', 'execute'))

    client.post('/needs', data={'needs': json.dumps(needs),
                                'application-key': app_key})

    rv = client.delete('/needs', data={'needs': json.dumps(needs),
                                       'application-key': app_key})

    assert rv.status_code == 200, str(rv.data)
    data = json.loads(rv.data.decode('utf-8'))
    assert not set(map(tuple, data['needs'])).issuperset(set(needs))
