import datetime

from flask import current_app as app, abort
from flask_restful import reqparse
import itsdangerous

from ..api import restful, db
from ..models import Persona
from ..signals import user_validated
from ..utils import md5
from ..utils import read_token


class RegisterValidate(restful.Resource):

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('token', type=str, required=True)
        args = parser.parse_args()

        try:
            uid, email = read_token(args['token'],
                                    salt=app.config['REGISTER_USER_TOKEN_SALT'])
        except itsdangerous.BadSignature as err:
            abort(400, 'invalid token')

        user = db.session.query(Persona).filter_by(id=uid).one()

        if user.validated_at:
            abort(409, 'account alredy activated')
        if md5(user.email) == email:
            user.validated_at = datetime.datetime.utcnow()
            user.active = True
            db.session.commit()
            user_validated.send(app._get_current_object(), user=user)

        return {'message': 'account activated'}
