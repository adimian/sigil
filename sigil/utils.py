from itsdangerous import URLSafeSerializer
from flask import request, current_app as app


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
