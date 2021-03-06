import json

from sigil.api import mail
from sigil.models import User
from sigil.multifactor import get_code


def preload_user(client):
    session = client._db.session
    user = User(username='eric',
                email='eric@adimian.com')
    user.password = 'secret'
    user.active = True
    session.add(user)
    session.commit()
    return user


def test_login_password(client):
    preload_user(client)
    rv = client.post('/login', data={'username': 'eric',
                                     'password': 'secret'})

    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['token']


def test_login_password_bad_user(client):
    preload_user(client)
    rv = client.post('/login', data={'username': 'maarten',
                                     'password': 'secret'})

    assert rv.status_code == 403


def test_login_password_bad_pass(client):
    preload_user(client)
    rv = client.post('/login', data={'username': 'eric',
                                     'password': 'zesecret'})

    assert rv.status_code == 403


def test_login_inactive(client):
    user = preload_user(client)
    user.active = False
    client._db.session.commit()
    rv = client.post('/login', data={'username': 'eric',
                                     'password': 'secret'})

    assert rv.status_code == 403


def test_login_password_2fa(client):
    user = preload_user(client)
    client.application.config['ENABLE_2FA'] = True

    rv = client.post('/login', data={'username': 'eric',
                                     'totp': get_code(user.totp_secret),
                                     'password': 'secret'})
    assert rv.status_code == 200, str(rv.data)


def test_token(client):
    user = preload_user(client)
    client._db.session.commit()

    rv = client.post('/login', data={'key': user.api_key})

    assert rv.status_code == 200


def test_recover_account_by_email(client):
    with mail.record_messages() as outbox:
        preload_user(client)
        rv = client.get('/user/recover', data={'email': 'eric@adimian.com'})
        assert rv.status_code == 200, str(rv.data)
        session = client._db.session
        user = session.query(User).filter_by(email='eric@adimian.com').one()
        assert outbox[0].send_to == set(['eric@adimian.com'])


def test_recover_account_by_username(client):
    with mail.record_messages() as outbox:
        preload_user(client)
        rv = client.get('/user/recover', data={'email': 'eric'})
        assert rv.status_code == 200, str(rv.data)
        session = client._db.session
        user = session.query(User).filter_by(email='eric@adimian.com').one()
        assert outbox[0].send_to == set(['eric@adimian.com'])
