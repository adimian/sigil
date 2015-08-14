from sigil.api import app, db
from sigil.models import User
from sqlalchemy.orm.exc import NoResultFound
import pytest


@pytest.fixture(scope='function')
def client(request):
    app.config['DEBUG'] = True
    db.create_all()

    db.session.add(User('user1', 'Secret', 'test@test.com'))
    db.session.add(User('user2', 'Secret', 'test1@test.com'))
    db.session.commit()

    client = app.test_client()
    client._db = db

    def finalize():
        # drop the database before the next test
        db.drop_all()
    request.addfinalizer(finalize)

    return client

