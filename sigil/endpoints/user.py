import datetime
import json

from flask import abort
from flask import current_app as app
import itsdangerous
import sqlalchemy

from . import ManagedResource, reqparse, AnonymousResource
from ..api import db
from ..models import AppContext, User, Need
from ..signals import password_recovered
from ..utils import current_user, read_token, md5


def get_target_user():
    parser = reqparse.RequestParser()
    parser.add_argument('username', type=str)
    args = parser.parse_args()

    if args['username']:
        user = User.by_username(args['username'])
    else:
        user = current_user
    return user


class UpdatePassword(AnonymousResource):

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('token', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        args = parser.parse_args()

        try:
            uid, email = read_token(args['token'],
                                    salt=app.config['UPDATE_PASSWORD_TOKEN_SALT'])
        except itsdangerous.BadSignature as err:
            abort(400, 'invalid token')

        user = db.session.query(User).filter_by(id=uid).one()

        if not user.must_change_password:
            abort(409, 'password already updated')
        if md5(user.email) == email:
            user.validated_at = datetime.datetime.utcnow()
            user.password = args['password']
            user.must_change_password = False
            db.session.commit()
            password_recovered.send(app._get_current_object(), user=user)
        else:
            abort(400,
                  'you main e-mail address has been changed since '
                  'the request has been issued, you should start again')

        return {'message': 'password updated !'}


class UserDetails(ManagedResource):
    def get(self):
        user = get_target_user()
        return {'firstname': user.fn,
                'lastname': user.sn,
                'username': user.username,
                'displayname': user.display_name,
                'id': user.id}


class UserPermissions(ManagedResource):
    def get(self):
        user = get_target_user()
        parser = reqparse.RequestParser()
        parser.add_argument('context', type=str, required=True)
        args = parser.parse_args()
        return {'provides': user.provides(args['context'])}

    def update_permissions(self, mode):
        user = get_target_user()
        parser = reqparse.RequestParser()
        parser.add_argument('context', type=str, required=True)
        parser.add_argument('needs', type=str, required=True)
        args = parser.parse_args()

        try:
            ctx = AppContext.query.filter_by(name=args['context']).one()
        except sqlalchemy.orm.exc.NoResultFound as err:
            abort(400, 'application not found')

        request_needs = set(map(tuple, json.loads(args['needs'])))
        selected_needs = []
        for need in Need.query.filter_by(app_context=ctx).all():
            nat = need.as_tuple()
            if nat in request_needs:
                selected_needs.append(need)
                request_needs.remove(nat)

        if request_needs:
            abort(400,
                  'permissions {} were not found'.format(repr(request_needs)))

        for need in selected_needs:
            if mode == 'add':
                user.permissions.append(need)
            elif mode == 'delete':
                user.permissions.remove(need)

        db.session.commit()

        return {'provides': user.provides(args['context'])}

    def post(self):
        return self.update_permissions(mode='add')

    def delete(self):
        return self.update_permissions(mode='delete')
