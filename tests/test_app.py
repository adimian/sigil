def test_register_app(client):
    rv = client.post('/app/register', data={'name': 'newapp'},
                     headers=client._auth_headers)

    assert rv.status_code == 200
