from functools import wraps
import hashlib
import uuid

from flask import request, current_app as app, abort
from itsdangerous import URLSafeSerializer
import sqlalchemy


def get_remote_ip():
    return (request.environ.get('HTTP_X_REAL_IP') or
            request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr))


def generate_token(data, salt):
    serializer = URLSafeSerializer(app.config['SECRET_KEY'],
                                   salt=salt)
    return serializer.dumps(data)


def read_token(data, salt):
    serializer = URLSafeSerializer(app.config['SECRET_KEY'],
                                   salt=salt)
    return serializer.loads(data)


def md5(string):
    return hashlib.md5(string.encode('utf-8')).hexdigest()


def sha256(string):
    return hashlib.sha256(string.encode('utf-8')).hexdigest()


def random_token():
    return sha256(str(uuid.uuid4()))


def requires_authentication(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        token = request.headers.get('Authentication-Token')
        if not token:
            abort(401, 'missing Authentication-Token header')

        from .models import UserSession
        try:
            session = UserSession.query.filter_by(token=token).one()
        except sqlalchemy.orm.exc.NoResultFound as err:
            abort(401, 'session expired')

        return func(*args, **kwargs)
    return decorated_view
