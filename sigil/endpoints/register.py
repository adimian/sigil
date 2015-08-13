from flask import current_app as app, abort
from flask_restful import reqparse
import sqlalchemy

from ..api import restful, db
from ..models import Persona, User
from ..signals import user_registered
from ..utils import generate_token


class Register(restful.Resource):

    def post(self, persona_class):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        parser.add_argument('email', type=str, required=True)

        parser.add_argument('surname', type=str)

        args = parser.parse_args()

        klass = {'persona': Persona,
                 'user': User}.get(persona_class)

        if not klass:
            raise Exception('unknown persona type {0}'.format(persona_class))

        try:
            user = klass(name=args['name'],
                         password=args['password'],
                         email=args['email'])
            if isinstance(user, User):
                    user.surname = args['surname']
        except ValueError as err:
            abort(400, str(err))

        db.session.add(user)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError as err:
            message = 'an account with the same name/email already exists'
            abort(409, message)

        token = generate_token(user.id,
                               salt=app.config['REGISTER_USER_TOKEN_SALT'])

        user_registered.send(app._get_current_object(), user=user, token=token)

        return {"status": 1,
                "token": token}

