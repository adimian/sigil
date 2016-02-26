import datetime
import json
import logging

from flask import abort
from flask import current_app as app
from flask_principal import Permission
import itsdangerous
from sqlalchemy import or_
import sqlalchemy

from . import ManagedResource, reqparse, AnonymousResource, ProtectedResource
from ..api import db
from ..models import AppContext, User, Need
from ..multifactor import qr_code_for_user, check_code, send_sms_code
from ..signals import password_recovered, user_request_password_recovery
from ..utils import current_user, read_token, md5, generate_token, get_remote_ip

logger = logging.getLogger(__name__)


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


def user_by_token(token):
    try:
        salt = app.config['UPDATE_PASSWORD_TOKEN_SALT']
        (uid, email), timestamp = read_token(token, salt=salt,
                                             return_timestamp=True)
    except itsdangerous.BadSignature:
        abort(400, 'invalid token')
    try:
        user = db.session.query(User).filter_by(id=uid).one()
    except sqlalchemy.orm.exc.NoResultFound:
        abort(404, 'unknown user')
    if user.token_gen_date is not None and timestamp < user.token_gen_date:
        abort(400, 'replaced token')
    return user, email


class UserAPIKey(ManagedResource):
    def get(self):
        return {'key': current_user.api_key}

    def post(self):
        current_user.update_api_key()
        db.session.commit()
        return {'key': current_user.api_key}


class UserPassword(ManagedResource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('old_password', type=str, required=True)
        parser.add_argument('new_password', type=str, required=True)
        args = parser.parse_args()

        if current_user.is_correct_password(args['old_password']):
            current_user.password = args['new_password']
            db.session.commit()
            logger.info('user {} has changed password ({})'.format(current_user.username,
                                                                   get_remote_ip()))
        else:
            abort(400, 'wrong old password')


class MultifactorSendSMS(AnonymousResource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str)
        parser.add_argument('token', type=str)
        args = parser.parse_args()

        if args['username']:
            user = User.by_username(args['username'])
        elif args['token']:
            user, _ = user_by_token(args['token'])

        if not user:
            abort(404, 'unknown user')
        if not user.mobile_number:
            abort(404, 'no mobile phone number available for {}'.format(user.username))

        send_sms_code(user)


class MultifactorMethodConfirm(AnonymousResource):

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('token', type=str, required=True)
        parser.add_argument('totp', type=str, required=True)
        args = parser.parse_args()

        user, email = user_by_token(args['token'])

        if md5(user.email) == email:
            if check_code(user.totp_secret, args['totp']):
                user.totp_configured = True
                db.session.commit()
            else:
                abort(400, 'invalid totp code')
        else:
            abort(400,
                  'you main e-mail address has been changed since '
                  'the request has been issued, you should start again')


class ValidateUser(AnonymousResource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True)
        args = parser.parse_args()

        try:
            user = db.session.query(User).filter_by(email=args['email']).one()
        except sqlalchemy.orm.exc.NoResultFound:
            user = User.by_username(args['email'])
            if user is None:
                abort(404, 'user not found')

        # invalidate all previously emitted tokens
        user.token_gen_date = datetime.datetime.utcnow()

        token = generate_token([user.id, md5(user.email)],
                               salt=app.config['UPDATE_PASSWORD_TOKEN_SALT'])

        user_request_password_recovery.send(app._get_current_object(),
                                            user=user,
                                            token=token)
        db.session.commit()
        return {'token': token}

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('token', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        args = parser.parse_args()

        user, email = user_by_token(args['token'])

        if md5(user.email) == email:
            user.validated_at = datetime.datetime.utcnow()
            user.password = args['password']
            # invalidate all existing tokens
            user.token_gen_date = datetime.datetime.utcnow()
            db.session.commit()
            password_recovered.send(app._get_current_object(), user=user)
        else:
            abort(400,
                  'you main e-mail address has been changed since '
                  'the request has been issued, you should start again')

        return {'qrcode':  qr_code_for_user(user)}


class Reset2FA(ProtectedResource):
    def post(self):
        user = get_target_user()
        user.reset_otp()

        token = generate_token([user.id, md5(user.email)],
                               salt=app.config['UPDATE_PASSWORD_TOKEN_SALT'])
        return {'qrcode':  qr_code_for_user(user),
                'token': token}


class UserDetails(ManagedResource):
    def get(self):
        user = get_target_user()
        return user.public()

    def cleanup_active(self, new_value):
        return new_value == 'true'

    def post(self):
        user = get_target_user()
        fields = user.ALLOWED
        parser = reqparse.RequestParser()
        for field in fields:
            parser.add_argument(field, type=str)
        args = parser.parse_args()

        for field in fields:
            if args[field]:
                old, new = args[field], getattr(user, field)
                cleanup = getattr(self, 'cleanup_{}'.format(field), None)
                if cleanup:
                    new = cleanup(new)
                if old != new:
                    setattr(user, field, args[field])
        db.session.commit()
        return user.public()


class UserCatalog(ProtectedResource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('query', type=str)
        parser.add_argument('context', type=str)
        args = parser.parse_args()

        with Permission(('users', 'read')).require(403):
            users = []
            if not args['query']:
                for user in User.query.all():
                    users.append(user.public(args['context']))
            else:
                text = '%{}%'.format(args['query'])

                query = User.query.filter(or_(User.username.ilike(text),
                                              User.firstname.ilike(text),
                                              User.surname.ilike(text)))
                for user in query.all():
                    users.append(user.public(args['context']))

            return {'users': users}


class UserPermissions(ManagedResource):
    def options(self):
        user = get_target_user()
        response = {}
        for context in db.session.query(AppContext).all():
            response[context.name] = user.permission_catalog(context.name)
        return response

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
                if need not in user.permissions:
                    logger.debug('adding {}, was not in {}'.format(need, user.permissions))
                    user.permissions.append(need)
                else:
                    logger.debug('asked to add {}, but is already there, ignoring'.format(need))
            elif mode == 'delete':
                if need in user.permissions:
                    logger.debug('removing {}, was in {}'.format(need, user.permissions))
                    user.permissions.remove(need)
                else:
                    logger.debug('asked to remove {}, but is not there, ignoring'.format(need))

        db.session.commit()

        return {'provides': user.provides(args['context'])}

    def post(self):
        return self.update_permissions(mode='add')

    def delete(self):
        return self.update_permissions(mode='delete')
