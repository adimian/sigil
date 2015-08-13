import json
from sigil.models import User


def preload_user(client):
    user = User(name='eric',
                password='secret',
                email='eric@adimian.com')
    user.active = True
    client._db.session.add(user)
    client._db.session.commit()
    return user


def test_login_password(client):
    preload_user(client)
    rv = client.post('/test/login', data={'name': 'eric',
                                          'password': 'secret'})

    assert rv.status_code == 200


def test_login_password_bad_user(client):
    preload_user(client)
    rv = client.post('/test/login', data={'name': 'maarten',
                                          'password': 'secret'})

    assert rv.status_code == 403


def test_login_password_bad_pass(client):
    preload_user(client)
    rv = client.post('/test/login', data={'name': 'eric',
                                          'password': 'zesecret'})

    assert rv.status_code == 403


def test_login_inactive(client):
    user = preload_user(client)
    user.active = False
    client._db.session.commit()
    rv = client.post('/test/login', data={'name': 'eric',
                                          'password': 'secret'})

    assert rv.status_code == 403


def test_login_password_2fa(client):
    pass


def test_token(client):
    pass


def test_alias_password(client):
    pass
