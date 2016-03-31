import os
import shutil
from tempfile import mkdtemp

import pytest

from sigil.api import app, db, setup_endpoints
from sigil.emails import setup_emails
from sigil.models import User, Need
from sigil.permissions import setup_default_permissions
from sigil.utils import generate_token


setup_endpoints()
setup_emails()

ROOT_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="function")
def setup_templates(request):
    reg = b"reg {{creator}} {{user}} {{url}}"
    rec = b"rec {{creator}} {{user}} {{url}}"
    t = {"reg.html": reg, "rec.html": rec}
    root_path = os.path.join(ROOT_DIR, "templates")
    os.mkdir(root_path)
    for fn, content in t.items():
        file_path = os.path.join(root_path, fn)
        with open(file_path, 'wb+') as fh:
                fh.write(content)

    folder_orig_value = app.config['MAIL_TEMPLATE_FOLDER']
    templates_orig_value = app.config['MAIL_TEMPLATES']
    app.config['MAIL_TEMPLATE_FOLDER'] = root_path
    app.config['MAIL_TEMPLATES'] = {'REGISTER': 'reg.html',
                                    'RECOVER': 'rec.html'}

    def finalize():
        app.config['MAIL_TEMPLATE_FOLDER'] = folder_orig_value
        app.config['MAIL_TEMPLATES'] = templates_orig_value
        shutil.rmtree(root_path)
    request.addfinalizer(finalize)
    return True


@pytest.fixture(scope='function')
def client(request):
    app.config['DEBUG'] = True
    app.config['TESTING'] = True
    app.config['URL_PREFIX'] = ''
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    app.config['ENABLE_2FA'] = False
    app.config['LDAP_HOST'] = 'mocked.server'
    app.config['APP_KEYS_FOLDER'] = mkdtemp(prefix='sigil_keys_')
    db.create_all()

    with app.app_context():
        u1 = User('alice', 'test@test.com')
        u1.password = 'test'
        u2 = User('bernard', 'test1@test.com')
        u2.password = 'test'
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        client = app.test_client()
        client._db = db
        client._app = app

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

