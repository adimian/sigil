import datetime
import json

from flask import abort
from flask import current_app as app
from flask_principal import Permission
import itsdangerous
import sqlalchemy

from . import ManagedResource, reqparse, AnonymousResource, ProtectedResource
from ..api import db
from ..models import AppContext, User, Need
from ..signals import password_recovered, user_request_password_recovery
from ..utils import current_user, read_token, md5, generate_token
from ..multifactor import qr_code_for_user


def get_target_user():
    parser = reqparse.RequestParser()
    parser.add_argument('username', type=str)
    args = parser.parse_args()

    if args['username']:
        user = User.by_username(args['username'])
        if user is None:
            abort(404, 'unknown user {}'.format(args['username']))
    else:
        user = current_user
    return user


class UpdatePassword(AnonymousResource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True)
        args = parser.parse_args()

        try:
            user = db.session.query(User).filter_by(email=args['email']).one()
        except sqlalchemy.orm.exc.NoResultFound as err:
            abort(404, 'user not found')

        token = generate_token([user.id, md5(user.email)],
                               salt=app.config['UPDATE_PASSWORD_TOKEN_SALT'])

        user_request_password_recovery.send(app._get_current_object(),
                                            user=user,
                                            token=token)
        user.must_change_password = True
        db.session.commit()
        return {'token': token}

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

        response = {'message': 'password updated !'}
        if app.config['ENABLE_2FA']:
            response['qrcode'] = qr_code_for_user(user)
        return response


class UserDetails(ManagedResource):
    def get(self):
        user = get_target_user()
        return user.public()


class UserCatalog(ProtectedResource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('query', type=str)
        args = parser.parse_args()

        with Permission(('users', 'read')).require():
            users = []
            if not args['query']:
                for user in User.query.all():
                    users.append(user.public())
            else:
                text = args['query']
                query = User.query.filter(User.username.contains(text)).union(
                        User.query.filter(User.firstname.contains(text))).union(
                        User.query.filter(User.surname.contains(text)))
                for user in query.all():
                    users.append(user.public())

            return {'users': users}


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
