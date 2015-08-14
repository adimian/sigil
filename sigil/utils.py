import hashlib
import uuid

from flask import request, current_app as app
from itsdangerous import URLSafeSerializer


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


def new_api_key():
    return sha256(str(uuid.uuid4()))
