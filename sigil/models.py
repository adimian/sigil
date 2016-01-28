# @PydevCodeAnalysisIgnore
import datetime
import logging
import re

from flask import current_app as app
from flask_login import UserMixin
from flask_sqlalchemy import Model
from passlib.hash import ldap_sha512_crypt
from sqlalchemy import UniqueConstraint
import sqlalchemy
from sqlalchemy.event import listen
from sqlalchemy.ext.hybrid import hybrid_property

from .api import db, EXTRA_FIELDS
from .multifactor import new_user_secret
from .signals import user_registered
from .utils import random_token, generate_token, md5


logger = logging.getLogger(__name__)


class AccountMixin(object):
    def generate_token(self):
        token = generate_token([self.id, md5(self.email)],
                               salt=app.config['UPDATE_PASSWORD_TOKEN_SALT'])

        user_registered.send(app._get_current_object(), user=self, token=token)
        return token

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def _set_password(self, plaintext):
        self._password = ldap_sha512_crypt.encrypt(plaintext)

    def is_correct_password(self, plaintext):
        if not self._password:  # no password defined (new user)
            return False
        if ldap_sha512_crypt.verify(plaintext, self._password):
            return True
        return False

permissions = db.Table('permssions',
                       db.Column('user_id', db.Integer,
                                 db.ForeignKey('user.id')),
                       db.Column('need_id', db.Integer,
                                 db.ForeignKey('need.id')),
                       UniqueConstraint('user_id', 'need_id'),
                       )

group_member = db.Table('group_member',
                        
                        db.Column('group_id', db.Integer,
                                  db.ForeignKey('virtualgroup.id')),
                        db.Column('member_id', db.Integer,
                                  db.ForeignKey('user.id')),
                        UniqueConstraint('group_id', 'member_id'),
                        )

team_member = db.Table('team_member',
                       db.Column('team_id', db.Integer,
                                 db.ForeignKey('userteam.id')),
                       db.Column('member_id', db.Integer,
                                 db.ForeignKey('user.id')),
                       UniqueConstraint('team_id', 'member_id'),
                       )

extra_field = db.Table('extra_field',
                       db.Column('extrafield_id', db.Integer,
                                 db.ForeignKey('extrafield.id')),
                       db.Column('member_id', db.Integer,
                                 db.ForeignKey('user.id')),
                       UniqueConstraint('extrafield_id', 'member_id'),
                       )

class LDAPUserMixin(object):
    
    @property
    def ldap(self):
        # LDAP needs surname and givenname, so enforcing it
        data = {'surname': self.surname or self.username,
                'uid': self.username,
                'givenName': self.firstname or self.username,
                'displayName': self.display_name,
                'mail': self.email}
        if self.password:
            data['userPassword'] = self.password
        if self.mobile_number:
            data['mobile'] = self.mobile_number
        if self.totp_secret:
            data['totpSecret'] = self.totp_secret
        if self.totp_configured:
            data['totpEnabled'] = self.totp_configured
        return data


class User(UserMixin, AccountMixin, LDAPUserMixin, db.Model):
    PROTECTED = ('id', 'created_at', 'validated_at',
                 'totp_secret', 'username',
                 'password', 'api_key', 'groups', 'permissions', 'teams')
    # accounting fields
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean(), default=False)
    created_at = db.Column(db.DateTime(),
                           default=datetime.datetime.utcnow)
    validated_at = db.Column(db.DateTime())
    totp_secret = db.Column(db.String(256), default=new_user_secret)
    totp_configured = db.Column(db.Boolean(), default=False)

    # object fields
    description = db.Column(db.Text)
    username = db.Column(db.String(256), unique=True, nullable=False)
    _password = db.Column(db.String(256))
    email = db.Column(db.String(256), unique=True, nullable=False)
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
                                  backref=db.backref('users'))

    groups = db.relationship('VirtualGroup', secondary=group_member,
                             backref=db.backref('members'))

    teams = db.relationship('UserTeam', secondary=team_member,
                            backref=db.backref('members'))
    extra_fields = db.relationship('ExtraField', secondary=extra_field,
                                   lazy='dynamic')

    @classmethod
    def by_username(cls, username):
        username = username.strip().lower()
        try:
            return db.session.query(cls).filter_by(username=username).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return None

    def update_api_key(self):
        api_key = random_token()
        while self.__class__.query.filter_by(api_key=api_key).all():
            api_key = random_token()
        self.api_key = api_key

    def __init__(self, username, email, mobile_number=None):
        super(User, self).__init__()
        assert username
        assert email
        self.username = username.strip().lower()
        self.email = email.strip().lower()
        self.mobile_number = mobile_number

        # generate a new api key
        self.update_api_key()
        db.session.add(self)

    def __setattr__(self, key, value):
        if key in EXTRA_FIELDS:
            try:
                field = self.extra_fields.filter_by(field_name=key).one()
                field.value = value
            except sqlalchemy.orm.exc.NoResultFound:
                field = ExtraField(key, value)
                self.extra_fields.append(field)
        else:
            super().__setattr__(key, value)

    def __getattr__(self, key):
        if key in EXTRA_FIELDS:
            try:
                field = self.extra_fields.filter_by(field_name=key).one()
            except sqlalchemy.orm.exc.NoResultFound:
                return None
            return field.value
        else:
            return super().__getattribute__(key)

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

    def permission_catalog(self, context):
        ctx = AppContext.by_name(context)
        assert ctx, 'no context {}'.format(context)

        current_permissions = self.provides(context)
        return tuple([(p, p in current_permissions)
                     for p in ctx.declared_needs()])



    def __repr__(self):
        return '<{0} object: {1} [{2}]>'.format(self.__class__.__name__,
                                                self.display_name,
                                                self.id)

    def public(self, context=None):
        result = {'firstname': self.fn,
                  'lastname': self.sn,
                  'email': self.email,
                  'active': self.active,
                  'username': self.username,
                  'displayname': self.display_name,
                  'mobile': self.mobile_number,
                  'id': self.id,
                  'groups': [g.name for g in self.groups],
                  'teams': [g.name for g in self.teams]}
        if context:
            result['provides'] = self.provides(context)
        return result
    
    @property
    def ALLOWED(self):
        return set([x
                    for x in self._sa_class_manager.keys()
                    if not x.startswith('_')]) - set(self.PROTECTED)

    def reset_otp(self):
        self.totp_secret = new_user_secret()
        self.totp_configured = False
        db.session.add(self)
        db.session.commit()

        


class AppContext(db.Model):
    __tablename__ = 'appcontext'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)

    def __init__(self, name):
        self.name = name

    def declared_needs(self):
        return tuple(n.as_tuple() for n in self.needs)

    @classmethod
    def by_name(cls, name):
        try:
            return db.session.query(cls).filter_by(name=name).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return None


class Need(db.Model):
    __table_args__ = (UniqueConstraint('app_id', 'method',
                                       'value', 'resource'),)

    id = db.Column(db.Integer, primary_key=True)
    app_id = db.Column(db.Integer, db.ForeignKey('appcontext.id'))
    app_context = db.relationship('AppContext',
                                  backref=db.backref('needs'))
    method = db.Column(db.String(256))
    value = db.Column(db.String(256))
    resource = db.Column(db.String(256))

    @classmethod
    def by_tuple(cls, ctx, need_tuple):
        method, value = need_tuple[:2]
        if len(need_tuple) == 2:
            resource = '*'
        else:
            resource = need_tuple[2]
        try:
            return cls.query.filter_by(app_context=ctx,
                                       method=method,
                                       value=value,
                                       resource=resource).one()
        except sqlalchemy.orm.exc.NoResultFound as err:
            return None

    def __init__(self, app_context, method, value, resource=None):
        self.app_context = app_context
        self.method = method
        self.value = value
        self.resource = resource or "*"

    def __eq__(self, other):
        return (self.as_tuple() == other.as_tuple()
                and self.app_id == other.app_id)

    def as_tuple(self):
        if self.resource == '*':
            return (self.method, self.value)
        else:
            return (self.method, self.value, self.resource)

    @property
    def dotted(self):
        return '.'.join(self.as_tuple())

    def __repr__(self):
        return '<Need {}.{}>'.format(self.app_context.name,
                                     '.'.join(self.as_tuple()))

class VirtualGroup(db.Model):
    __tablename__ = 'virtualgroup'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)
    active = db.Column(db.Boolean(), default=True)

    @classmethod
    def by_name(cls, name):
        try:
            return db.session.query(cls).filter_by(name=name).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return None

    def __init__(self, name):
        self.name = name


class UserTeam(db.Model):
    __tablename__ = 'userteam'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)
    active = db.Column(db.Boolean(), default=True)

    def __init__(self, name):
        self.name = name


class ExtraField(db.Model):
    __tablename__ = 'extrafield'
    id = db.Column(db.Integer, primary_key=True)
    field_name = db.Column(db.String(256))
    value = db.Column(db.String(256))

    def __init__(self, field_name, value):
        self.field_name = field_name
        self.value = value


def validate_phone(target, value, oldvalue, initiator):
    if not value:
        return value
    return re.sub(r'[^+0-9]', '', value)

def validate_email(target, value, oldvalue, initiator):
    if "@" not in value or '.' not in value:
        raise ValueError('invalid email address')
    return value.lower().strip()

def force_lowercase(target, value, oldvalue, initiator):
    return value.lower().strip()

listen(User.mobile_number, 'set', validate_phone, retval=True)
listen(User.home_number, 'set', validate_phone, retval=True)
listen(User.phone_number, 'set', validate_phone, retval=True)
listen(User.email, 'set', validate_email, retval=True)

listen(User.username, 'set', force_lowercase, retval=True)
listen(VirtualGroup.name, 'set', force_lowercase, retval=True)
listen(UserTeam.name, 'set', force_lowercase, retval=True)
listen(ExtraField.field_name, 'set', force_lowercase, retval=True)
listen(AppContext.name, 'set', force_lowercase, retval=True)
listen(Need.method, 'set', force_lowercase, retval=True)
listen(Need.resource, 'set', force_lowercase, retval=True)
