from flask_principal import identity_loaded
from .utils import current_user
from .api import app
from itertools import product

INTERNAL_NEEDS = ('teams', 'users', 'appcontexts')

APP_MANDATORY_NEEDS = ('permissions',)


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    identity.user = current_user
    for need in current_user.permissions:
        identity.provides.add(need.as_tuple())


def setup_default_permissions():
    from .api import app, db
    from .models import AppContext, Need
    session = db.session
    ctx = AppContext(app.config['ROOT_APP_CTX'])
    session.add(ctx)

    for need in product(INTERNAL_NEEDS, ('read', 'write')):
        session.add(Need(ctx, *need))
    session.commit()

