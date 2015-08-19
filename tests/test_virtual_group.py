from sigil.models import VirtualGroup


def test_create_group(client):
    rv = client.post('/group',
                     data={'name': 'jabber'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)
    assert VirtualGroup.query.filter_by(name='jabber').one()
