import logging
import sys

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from raven.contrib.flask import Sentry

import flask_restful as restful

from .conf import configure


app = Flask('sigil')
configure(app)

if app.config['DEBUG']:
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

if app.config['SENTRY_DSN']:
    sentry = Sentry(app)


def setup_endpoints():
    logger.info('setting up endpoints')
    from .endpoints.register import Register
    from .endpoints.login import Login
    from .endpoints.user import (UserDetails, UserPermissions,
                                 UpdatePassword, UserCatalog)
    from .endpoints.appcontext import ApplicationContext, ApplicationNeeds
    from .endpoints.containers import VirtualGroupResource

    api = restful.Api(app)
    # application
    api.add_resource(ApplicationContext, '/app/register')
    api.add_resource(ApplicationNeeds, '/needs')
    # login (SSO)
    api.add_resource(Login, '/login')
    # user
    api.add_resource(Register, '/user/register')
    api.add_resource(UpdatePassword, '/user/recover', '/user/validate')
    api.add_resource(UserDetails, '/user/details')
    api.add_resource(UserPermissions, '/user/permissions')
    api.add_resource(UserCatalog, '/user')
    # containers
    api.add_resource(VirtualGroupResource, '/group')
    logger.info('endpoints ready')

setup_endpoints()
