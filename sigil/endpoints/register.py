from flask import current_app as app, abort
from sigil.api import restful, Persona, User, db
from flask_restful import reqparse
from sigil.signals import user_registered
from sigil.utils import generate_token
import sqlalchemy


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
            print(user)
        except sqlalchemy.exc.IntegrityError as err:
            message = 'an account of the same name already exists'
            abort(409, message)

        token = generate_token(user.id,
                               salt=app.config['REGISTER_USER_TOKEN_SALT'])

        user_registered.send(app._get_current_object(), user=user, token=token)

        return {"status": 1,
                "token": token}

