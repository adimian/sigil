import pytest

from sigil.api import app, db
from sigil.models import User, Need
from sigil.permissions import setup_default_permissions
from sigil.utils import generate_token


@pytest.fixture(scope='function')
def client(request):
    app.config['DEBUG'] = True
    app.config['TESTING'] = True
    db.create_all()

    u1 = User('alice', 'Secret', 'test@test.com')
    u2 = User('bernard', 'Secret', 'test1@test.com')
    db.session.add(u1)
    db.session.add(u2)
    db.session.commit()

    client = app.test_client()
    client._db = db

    with app.app_context():
        client._auth_token = generate_token([u1.id, 'abcdef'],
                                            app.config['SESSION_TOKEN_SALT'])
        headers = {app.config['SESSION_TOKEN_HEADER']: client._auth_token}
        client._auth_headers = headers

    # give all permissions to alice
    setup_default_permissions()

    user = db.session.query(User).filter_by(id=u1.id).one()
    for need in Need.query.all():
        user.permissions.append(need)
    db.session.commit()
    client._user = user

    def finalize():
        # drop the database before the next test
        db.drop_all()
    request.addfinalizer(finalize)

    return client

