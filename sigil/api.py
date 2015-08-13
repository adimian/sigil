import datetime
import logging

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import (login_required, UserMixin)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property

import flask_restful as restful

from .conf import configure


class ProtectedResource(restful.Resource):
    method_decorators = [login_required]

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG

app = Flask('sigil')
configure(app)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


class AccountMixin(object):
    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def _set_password(self, plaintext):
        self._password = bcrypt.generate_password_hash(plaintext)

    def is_correct_password(self, plaintext):
        if bcrypt.check_password_hash(self._password, plaintext):
            return True
        return False


class Persona(UserMixin, AccountMixin, db.Model):
    # accounting fields
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)

    active = db.Column(db.Boolean(), default=False)
    created_at = db.Column(db.DateTime(),
                           default=datetime.datetime.utcnow())
    confirmed_at = db.Column(db.DateTime())

    # object fields
    name = db.Column(db.String(255), unique=True)
    _password = db.Column(db.String(255))
    mail = db.Column(db.String(255), unique=True)

    def __init__(self, name, password, email):
        super(Persona, self).__init__()
        self.name = name
        self.password = password
        self.email = email

    @property
    def cn(self):
        return self.name

    @property
    def dn(self):
        return self.name

    @property
    def sn(self):
        return self.name

    @property
    def display_name(self):
        return '{0} {1}'.format(self.name, self.sn)

    def __repr__(self):
        return '<{0} object: {1} [{2}]>'.format(self.__class__.__name__,
                                                self.display_name,
                                                self.id)


class User(Persona):
    jpeg_photo = db.Column(db.LargeBinary)
    surname = db.Column(db.String(255))

    phone_number = db.Column(db.String(255))
    mobile_number = db.Column(db.String(255))
    home_number = db.Column(db.String(255))

    @property
    def sn(self):
        return self.surname


def setup_endpoints():
    from .endpoints.register import Register

    api = restful.Api(app)
    api.add_resource(Register, '/<string:persona_class>/register')

setup_endpoints()
