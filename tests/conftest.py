from sigil.api import app, db
from sigil.models import Persona, User
from sqlalchemy.orm.exc import NoResultFound
import pytest


@pytest.fixture(scope='function')
def client(request):
    db.create_all()
    try:
        Persona.query.filter_by(name='me').one()
    except NoResultFound:
        db.session.add(Persona('app1', 'Secret', 'test@test.com'))
        db.session.add(User('user1', 'Secret', 'test1@test.com'))
        db.session.commit()
    client = app.test_client()
    client._db = db

    def finalize():
        # drop the database before the next test
        db.drop_all()
    request.addfinalizer(finalize)

    return client

