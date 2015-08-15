from flask import abort, request, current_app as app
from flask_restful import reqparse
import sqlalchemy

from ..api import restful, db
from ..utils import random_token, generate_token
from ..models import User


class Login(restful.Resource):

    def post(self, context):
        session = db.session
        parser = reqparse.RequestParser()

        parser.add_argument('username', type=str)
        parser.add_argument('password', type=str)
        parser.add_argument('totp', type=str)
        # OR
        parser.add_argument('key', type=str)

        args = parser.parse_args()

        if args['username'] and args['password']:
            try:
                user = session.query(User).filter_by(username=args['username']).one()
            except sqlalchemy.orm.exc.NoResultFound as err:
                abort(403, 'invalid user')
            if not user.is_correct_password(args['password']):
                abort(403, 'invalid password')
            if not user.active:
                abort(403, 'inactive user')
        elif args['key']:
            try:
                user = session.query(User).filter_by(api_key=args['key']).one()
            except sqlalchemy.orm.exc.NoResultFound as err:
                abort(403, 'invalid API key')
        else:
            abort(400, 'no authentication method found')

        # handle session
        token = generate_token([user.id, random_token()],
                               app.config['SESSION_TOKEN_SALT'])

        return {'token': token}

