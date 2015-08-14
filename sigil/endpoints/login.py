from flask import abort
from flask_restful import reqparse
import sqlalchemy

from ..api import restful, db
from ..models import Persona


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
                user = session.query(Persona).filter_by(name=args['name']).one()
            except sqlalchemy.orm.exc.NoResultFound as err:
                abort(403, 'invalid user')
            if not user.is_correct_password(args['password']):
                abort(403, 'invalid password')
            if not user.active:
                abort(403, 'inactive user')
        elif args['key']:
            try:
                user = session.query(Persona).filter_by(api_key=args['key']).one()
            except sqlalchemy.orm.exc.NoResultFound as err:
                abort(403, 'invalid user')
        else:
            abort(400, 'no authentication method found')
