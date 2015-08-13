import json


def test_login_password(client):
    rv = client.post('/login', data={'name': 'eric',
                                     'password': 'secret'})

    assert rv.status_code == 200


def test_login_password_2fa(client):
    pass


def test_token(client):
    pass


def test_alias_password(client):
    pass
