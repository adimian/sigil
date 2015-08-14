import json
from sigil.models import Persona


def preload_user(client):
    session = client._db.session
    user = Persona(name='eric',
                   password='secret',
                   email='eric@adimian.com')
    user.active = True
    session.add(user)
    session.commit()
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
    user = preload_user(client)
    client._db.session.commit()

    rv = client.post('/test/login', data={'key': user.api_key})

    assert rv.status_code == 200


def test_alias_password(client):
    pass
