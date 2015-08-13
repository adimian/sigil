import json


def test_register_user(client):
    rv = client.post('/user/register', data={'name': 'eric',
                                             'surname': 'gazoni',
                                             'password': 'secret',
                                             'email': 'eric@adimian.com'})
    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['token']


def test_register_app(client):
    rv = client.post('/persona/register', data={'name': 'eric',
                                                'password': 'secret',
                                                'email': 'eric@adimian.com'})
    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['token']


def test_register_existing(client):
    rv = client.post('/persona/register', data={'name': 'eric',
                                                'password': 'secret',
                                                'email': 'eric@adimian.com'})
    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['token']

    rv = client.post('/persona/register', data={'name': 'eric',
                                                'password': 'secret',
                                                'email': 'eric@adimian.com'})
    assert rv.status_code == 409


def test_register_error(client):
    rv = client.post('/persona/register', data={'name': '',
                                                'password': '',
                                                'email': ''})
    assert rv.status_code == 400
