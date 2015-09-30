import logging
import os
import sys

from flask import Flask, send_from_directory, safe_join
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

if app.config['SERVE_STATIC']:
    # static files
    @app.route('{}/'.format(app.config['UI_URL_PREFIX']))
    @app.route('{}/<path:path>'.format(app.config['UI_URL_PREFIX']))
    def serve(path=""):
        d = os.path.dirname
        root = d(d(os.path.abspath(__file__)))
        file = os.path.basename(path)
        path = d(path)
        if not file:
            file = 'index.html'
        path = safe_join(safe_join(root, 'ui'), path)
        print(path, file)
        return send_from_directory(path, file)


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
