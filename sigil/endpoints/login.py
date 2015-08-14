from flask import abort, request
from flask_restful import reqparse
import sqlalchemy

from ..api import restful, db
from ..utils import random_token
from ..models import User, UserSession


class Login(restful.Resource):

    def post(self, context):
        session = db.session
        parser = reqparse.RequestParser()

        parser.add_argument('name', type=str)
        parser.add_argument('password', type=str)
        parser.add_argument('totp', type=str)
        # OR
        parser.add_argument('key', type=str)

        args = parser.parse_args()

        if args['name'] and args['password']:
            try:
                user = session.query(User).filter_by(name=args['name']).one()
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
        user_sessions = UserSession.query.filter_by(user=user).all()
        for user_session in user_sessions:
            db.session.delete(user_session)

        new_session = UserSession(user=user, token=random_token())
        db.session.add(new_session)
        db.session.commit()

        return {'token': new_session.token}

