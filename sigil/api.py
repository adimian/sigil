import logging
import sys

from flask import Flask
from flask_alembic import Alembic
from flask_mail import Mail
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
mail = Mail(app)
alembic = Alembic(app)

sentry = None
if app.config['SENTRY_DSN']:
    logger.info('Sentry is active')
    sentry = Sentry(app)
else:
    logger.info('Sentry is inactive')


def setup_endpoints():
    logger.info('setting up endpoints')
    from .endpoints.register import Register
    from .endpoints.login import Login
    from .endpoints.user import (UserDetails, UserPermissions, UserPassword,
                                 ValidateUser, UserCatalog, UserAPIKey,
                                 MultifactorMethodConfirm, MultifactorSendSMS)
    from .endpoints.appcontext import ApplicationContext, ApplicationNeeds
    from .endpoints.containers import (VirtualGroupResource,
                                       VirtualGroupMembers, UserTeamResource,
                                       UserTeamMembers)
    from .endpoints.options import ServerOptions
    from .endpoints.connectors import ExcelImport, ExcelExport, ExcelDownload

    api = restful.Api(app, prefix=app.config['API_URL_PREFIX'])
    # application
    api.add_resource(ApplicationContext, '/app', '/app/register')
    api.add_resource(ApplicationNeeds, '/needs')
    api.add_resource(ServerOptions, '/options')
    # login (SSO)
    api.add_resource(Login, '/login')
    # user
    api.add_resource(Register, '/user/register')
    api.add_resource(MultifactorMethodConfirm, '/user/2fa/confirm')
    api.add_resource(MultifactorSendSMS, '/user/2fa/sms')
    api.add_resource(ValidateUser, '/user/recover', '/user/validate')
    api.add_resource(UserPassword, '/user/password')
    api.add_resource(UserDetails, '/user/details')
    api.add_resource(UserAPIKey, '/user/key')
    api.add_resource(UserPermissions, '/user/permissions')
    api.add_resource(UserCatalog, '/user', '/user/search')
    # containers
    api.add_resource(VirtualGroupResource, '/group')
    api.add_resource(VirtualGroupMembers, '/group/members')
    api.add_resource(UserTeamResource, '/team')
    api.add_resource(UserTeamMembers, '/team/members')
    # connectors
    api.add_resource(ExcelImport, '/import/excel')
    api.add_resource(ExcelExport, '/export/excel')
    api.add_resource(ExcelDownload, '/download/excel')
    logger.info('endpoints ready')
