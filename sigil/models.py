import datetime
import logging

from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.schema import UniqueConstraint

from sigil.utils import random_token

from .api import db, bcrypt


logger = logging.getLogger(__name__)


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

permissions = db.Table('permssions',
                       db.Column('user_id', db.Integer,
                                 db.ForeignKey('user.id')),
                       db.Column('need_id', db.Integer,
                                 db.ForeignKey('need.id'))
)


class User(UserMixin, AccountMixin, db.Model):
    # accounting fields
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)

    active = db.Column(db.Boolean(), default=False)
    created_at = db.Column(db.DateTime(),
                           default=datetime.datetime.utcnow())
    validated_at = db.Column(db.DateTime())

    # object fields
    username = db.Column(db.String(256), unique=True)
    _password = db.Column(db.String(256))
    email = db.Column(db.String(256), unique=True)
    api_key = db.Column(db.String(256), unique=True)

    # user fields
    jpeg_photo = db.Column(db.LargeBinary)
    firstname = db.Column(db.String(256))
    surname = db.Column(db.String(256))
    display = db.Column(db.String(256))

    phone_number = db.Column(db.String(256))
    mobile_number = db.Column(db.String(256))
    home_number = db.Column(db.String(256))

    permissions = db.relationship('Need', secondary=permissions,
                                  backref=db.backref('users', lazy='dynamic'))

    @classmethod
    def by_username(cls, username):
        return cls.query.filter_by(username=username).one()

    def __init__(self, username, password, email):
        super(User, self).__init__()
        self.username = username
        self.password = password
        self.email = email

        api_key = random_token()
        while self.__class__.query.filter_by(api_key=api_key).all():
            api_key = random_token()
        self.api_key = api_key

    @property
    def cn(self):
        return self.username

    @property
    def dn(self):
        return self.username

    @property
    def sn(self):
        return self.surname or self.username

    @property
    def fn(self):
        return self.firstname or self.username

    @property
    def display_name(self):
        return self.display or '{0} {1}'.format(self.fn, self.sn)

    def provides(self, context):
        return tuple(p.as_tuple() for p in self.permissions
                     if p.app_context.name == context)

    def __repr__(self):
        return '<{0} object: {1} [{2}]>'.format(self.__class__.__name__,
                                                self.display_name,
                                                self.id)


class AppContext(db.Model):
    __tablename__ = 'appcontext'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)

    def __init__(self, name):
        self.name = name

    def show(self):
        return tuple(n.as_tuple() for n in self.needs)


class Need(db.Model):
    __table_args__ = (UniqueConstraint('app_id', 'method',
                                       'value', 'resource'),)

    id = db.Column(db.Integer, primary_key=True)
    app_id = db.Column(db.Integer, db.ForeignKey('appcontext.id'))
    app_context = db.relationship('AppContext',
                                  backref=db.backref('needs', lazy='dynamic'))
    method = db.Column(db.String(256))
    value = db.Column(db.String(256))
    resource = db.Column(db.String(256))

    @classmethod
    def by_tuple(cls, need_tuple):
        method, value = need_tuple[:2]
        if len(need_tuple) == 2:
            resource = '*'
        else:
            resource = need_tuple[2]
        return cls.query.filter_by(method=method,
                                   value=value,
                                   resource=resource).one

    def __init__(self, app_context, method, value, resource=None):
        self.app_context = app_context
        self.method = method
        self.value = value
        self.resource = resource or "*"

    def as_tuple(self):
        if self.resource == '*':
            return (self.method, self.value)
        else:
            return (self.method, self.value, self.resource)

    def __repr__(self):
        return '<Need {}.{}>'.format(self.app_context.name,
                                     '.'.join(self.as_tuple()))
