import logging

from flask import abort, current_app as app
from flask_restful import reqparse
import sqlalchemy

from . import AnonymousResource
from ..api import db
from ..models import User
from ..multifactor import check_code
from ..signals import user_login
from ..utils import random_token, generate_token, get_remote_ip


logger = logging.getLogger(__name__)


class Login(AnonymousResource):

    def post(self):
        session = db.session
        parser = reqparse.RequestParser()

        parser.add_argument('username', type=str)
        parser.add_argument('password', type=str)
        parser.add_argument('totp', type=str)
        # OR
        parser.add_argument('key', type=str)

        args = parser.parse_args()

        logger.info('login attempt from {}'.format(get_remote_ip()))

        if args['username'] and args['password']:
            try:
                user = session.query(User).filter_by(username=args['username']).one()
                logger.info('login by credentials: {}'.format(user.username))
            except sqlalchemy.orm.exc.NoResultFound:
                abort(403, 'invalid user: {}'.format(args['username']))
            if not user.password:
                abort(403, ('you need to activate your account now, '
                            'please use the link you received by e-mail'))
            if not user.is_correct_password(args['password']):
                abort(403, 'invalid password')
            if app.config['ENABLE_2FA'] and user.totp_configured:
                if not args['totp']:
                    abort(400, 'TOTP code required')
                if not check_code(user.totp_secret, args['totp']):
                    abort(403, 'invalid TOTP code')
        elif args['key']:
            try:
                user = session.query(User).filter_by(api_key=args['key']).one()
                logger.info('login by api key: {}'.format(user.username))
            except sqlalchemy.orm.exc.NoResultFound:
                abort(403, 'invalid API key')
        else:
            abort(400, 'no authentication method found')

        if not user.active:
            abort(403, 'inactive user')

        # handle session
        token = generate_token([user.id, random_token()],
                               app.config['SESSION_TOKEN_SALT'])

        user_login.send(app._get_current_object(), user=user)

        return {'token': token}

