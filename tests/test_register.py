import json


def test_register_user(client):
    rv = client.post('/user/register', data={'username': 'eric',
                                             'surname': 'gazoni',
                                             'password': 'secret',
                                             'email': 'eric@adimian.com'})
    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['token']


def test_validate(client):
    rv = client.post('/user/register', data={'username': 'eric',
                                             'surname': 'gazoni',
                                             'password': 'secret',
                                             'email': 'eric@adimian.com'})
    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['token']

    rv = client.post('/validate', data={'token': data['token']})
    assert rv.status_code == 200


def test_validate_error(client):
    rv = client.post('/user/register', data={'username': 'eric',
                                             'surname': 'gazoni',
                                             'password': 'secret',
                                             'email': 'eric@adimian.com'})
    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['token']

    rv = client.post('/validate', data={'token': 'nope'})
    assert rv.status_code == 400


def test_validate_twice(client):
    rv = client.post('/user/register', data={'username': 'eric',
                                             'surname': 'gazoni',
                                             'password': 'secret',
                                             'email': 'eric@adimian.com'})
    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['token']

    rv = client.post('/validate', data={'token': data['token']})
    assert rv.status_code == 200

    rv = client.post('/validate', data={'token': data['token']})
    assert rv.status_code == 409


def test_register_existing(client):
    rv = client.post('/user/register', data={'username': 'eric',
                                             'password': 'secret',
                                             'email': 'eric@adimian.com'})
    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['token']

    rv = client.post('/user/register', data={'username': 'eric',
                                             'password': 'secret',
                                             'email': 'eric@adimian.com'})
    assert rv.status_code == 409


def test_register_error(client):
    rv = client.post('/user/register', data={'username': '',
                                                'password': '',
                                                'email': ''})
    assert rv.status_code == 400
