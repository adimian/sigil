from flask import current_app as app, abort
from flask_principal import Permission
from flask_restful import reqparse
import sqlalchemy

from . import ProtectedResource
from ..api import db
from ..models import User


class Register(ProtectedResource):

    def post(self):
        with Permission(('users', 'write')).require():
            parser = reqparse.RequestParser()
            parser.add_argument('username', type=str, required=True)
            parser.add_argument('email', type=str, required=True)
            parser.add_argument('mobile_number', type=str,
                                required=app.config['ENABLE_2FA'])

            args = parser.parse_args()

            if not args['username']:
                abort(400, 'missing username')
            if not args['email']:
                abort(400, 'missing email')

            try:
                user = User(username=args['username'],
                            email=args['email'],
                            mobile_number=args['mobile_number'])
                if app.config['AUTO_ACTIVATE_NEW_USER']:
                    user.active = True
            except ValueError as err:
                abort(400, str(err))

            db.session.add(user)
            try:
                db.session.commit()
            except sqlalchemy.exc.IntegrityError as err:
                message = 'an account with the same username/email already exists'
                abort(409, message)

            token = user.generate_token()

            return {"token": token}

