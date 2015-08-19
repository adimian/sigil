from itertools import product
import logging

from flask_principal import identity_loaded

from .api import app
from .models import Need
from .utils import current_user


INTERNAL_NEEDS = ('teams', 'groups', 'users', 'appcontexts')

APP_MANDATORY_NEEDS = ('permissions',)

logger = logging.getLogger(__name__)


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    identity.user = current_user
    for need in current_user.provides(app.config['ROOT_APP_CTX']):
        identity.provides.add(need)

    if app.config['DEBUG'] and not app.config['TESTING']:
        logging.warning('running in DEBUG mode, all users automatically '
                        'get full permissions '
                        '(do not use this setting in production)')
        for need in Need.query.all():
            identity.provides.add(need.as_tuple())


def setup_default_permissions():
    from .api import app, db
    from .models import AppContext, Need
    session = db.session
    if not AppContext.query.filter_by(name=app.config['ROOT_APP_CTX']).first():
        ctx = AppContext(app.config['ROOT_APP_CTX'])
        session.add(ctx)

        for need in product(INTERNAL_NEEDS, ('read', 'write')):
            session.add(Need(ctx, *need))
        session.commit()

