import json

from sigil.api import mail
from sigil.models import User
from sigil.multifactor import get_code


def test_register_user(client):
    with mail.record_messages() as outbox:
        rv = client.post('/user/register', data={'username': 'eric',
                                                 'email': 'eric@adimian.com'},
                         headers=client._auth_headers)
        assert rv.status_code == 200, str(rv.data)
        data = json.loads(rv.data.decode('utf-8'))
        assert data['token'] in outbox[0].html
        assert outbox[0].send_to == set(['eric@adimian.com'])
        assert "reg alice eric" not in outbox[0].html


def test_register_user_with_custom_template(client, setup_templates):
    with mail.record_messages() as outbox:
        rv = client.post('/user/register', data={'username': 'eric',
                                                 'email': 'eric@adimian.com'},
                         headers=client._auth_headers)
        assert rv.status_code == 200, str(rv.data)
        assert "reg alice eric" in outbox[0].html


def test_validate(client):
    rv = client.post('/user/register', data={'username': 'eric',
                                             'email': 'eric@adimian.com'},
                     headers=client._auth_headers)
    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['token']

    rv = client.post('/user/validate', data={'token': data['token'],
                                             'password': 'secret'})
    assert rv.status_code == 200


def test_validate_2fa(client):
    client.application.config['ENABLE_2FA'] = True
    rv = client.post('/user/register', data={'username': 'eric',
                                             'email': 'eric@adimian.com',
                                             'mobile_number': '1234'},
                     headers=client._auth_headers)
    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['token']

    rv = client.post('/user/validate', data={'token': data['token'],
                                             'password': 'secret'})
    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['qrcode']


def test_validate_2fa_bad_code(client):
    client.application.config['ENABLE_2FA'] = True
    rv = client.post('/user/register', data={'username': 'eric',
                                             'email': 'eric@adimian.com',
                                             'mobile_number': '1234'},
                     headers=client._auth_headers)
    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['token']

    rv = client.post('/user/2fa/confirm', data={'token': data['token'],
                                                'totp': '1111'})
    assert rv.status_code == 400, str(rv.data)


def test_validate_2fa_good_code(client):
    client.application.config['ENABLE_2FA'] = True
    rv = client.post('/user/register', data={'username': 'eric',
                                             'email': 'eric@adimian.com',
                                             'mobile_number': '1234'},
                     headers=client._auth_headers)
    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['token']

    user = User.by_username('eric')
    code = get_code(user.totp_secret)
    rv = client.post('/user/2fa/confirm', data={'token': data['token'],
                                                'totp': code})
    assert rv.status_code == 200, str(rv.data)
    assert User.by_username('eric').totp_configured


def test_send_sms_no_number(client):
    rv = client.post('/user/2fa/sms',
                     data={'username': client._user.username})
    assert rv.status_code == 404, str(rv.data)


def test_send_sms_with_number(client):
    client.application.config['ENABLE_2FA'] = True
    rv = client.post('/user/register', data={'username': 'eric',
                                             'email': 'eric@adimian.com',
                                             'mobile_number': '1234'},
                     headers=client._auth_headers)
    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))

    rv = client.post('/user/2fa/sms',
                     data={'username': 'eric'})
    assert rv.status_code == 200, str(rv.data)

    rv = client.post('/user/2fa/sms',
                     data={'token': data['token']})
    assert rv.status_code == 200, str(rv.data)


def test_validate_error(client):
    rv = client.post('/user/register', data={'username': 'eric',
                                             'password': 'secret',
                                             'email': 'eric@adimian.com'},
                     headers=client._auth_headers)
    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['token']

    rv = client.post('/user/validate', data={'token': 'nope'})
    assert rv.status_code == 400


def test_validate_twice(client):
    rv = client.post('/user/register', data={'username': 'eric',
                                             'email': 'eric@adimian.com'},
                     headers=client._auth_headers)
    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['token']

    rv = client.post('/user/validate', data={'token': data['token'],
                                             'password': 'something'})
    assert rv.status_code == 200

    rv = client.post('/user/validate', data={'token': data['token'],
                                             'password': 'somethingelse'})
    assert rv.status_code == 200


def test_register_existing(client):
    rv = client.post('/user/register', data={'username': 'eric',
                                             'email': 'eric@adimian.com'},
                     headers=client._auth_headers)
    assert rv.status_code == 200
    data = json.loads(rv.data.decode('utf-8'))
    assert data['token']

    rv = client.post('/user/register', data={'username': 'eric',
                                             'email': 'eric@adimian.com'},
                     headers=client._auth_headers)
    assert rv.status_code == 409


def test_register_error(client):
    rv = client.post('/user/register', data={'username': '',
                                             'email': ''},
                     headers=client._auth_headers)
    assert rv.status_code == 400
