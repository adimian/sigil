import json

from sigil.models import VirtualGroup, User


def test_create_group(client):
    rv = client.post('/group',
                     data={'name': 'jabber'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)
    assert VirtualGroup.query.filter_by(name='jabber').one()


def test_add_members(client):
    rv = client.post('/group',
                     data={'name': 'jabber'},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    rv = client.post('/group/members',
                     data={'name': 'jabber',
                           'usernames': json.dumps(['alice', 'bernard'])},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    user = client._db.session.query(User).filter_by(username='alice').one()
    assert [g.name for g in user.groups] == ['jabber']
