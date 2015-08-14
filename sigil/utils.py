from functools import wraps
import hashlib
import uuid

from werkzeug.local import LocalProxy
from flask import request, current_app as app, abort, _request_ctx_stack
from itsdangerous import URLSafeTimedSerializer
import sqlalchemy


def get_remote_ip():
    return (request.environ.get('HTTP_X_REAL_IP') or
            request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr))


def generate_token(data, salt):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'],
                                        salt=salt)
    return serializer.dumps(data)


def read_token(data, salt, max_age=None):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'],
                                        salt=salt)
    return serializer.loads(data, max_age=max_age)


def md5(string):
    return hashlib.md5(string.encode('utf-8')).hexdigest()


def sha256(string):
    return hashlib.sha256(string.encode('utf-8')).hexdigest()


def random_token():
    return sha256(str(uuid.uuid4()))


def _get_user():
    return getattr(_request_ctx_stack.top, 'user', None)
current_user = LocalProxy(lambda: _get_user())


def requires_authentication(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        token = request.headers.get('Authentication-Token')
        if not token:
            abort(401, 'missing Authentication-Token header')

        user_id, _ = read_token(token,
                                app.config['SESSION_TOKEN_SALT'],
                                app.config['SESSION_TOKEN_MAX_AGE'])

        from .models import User
        try:
            user = User.query.filter_by(id=user_id).one()
        except sqlalchemy.orm.exc.NoResultFound as err:
            abort(401, 'unknown user')

        _request_ctx_stack.top.user = user

        return func(*args, **kwargs)
    return decorated_view
