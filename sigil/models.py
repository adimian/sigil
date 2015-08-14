import datetime
import logging

from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property

from sigil.utils import new_api_key

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


class Persona(UserMixin, AccountMixin, db.Model):
    # accounting fields
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)

    active = db.Column(db.Boolean(), default=False)
    created_at = db.Column(db.DateTime(),
                           default=datetime.datetime.utcnow())
    validated_at = db.Column(db.DateTime())

    # object fields
    name = db.Column(db.String(255), unique=True)
    _password = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    api_key = db.Column(db.String(255), unique=True)

    def __init__(self, name, password, email):
        super(Persona, self).__init__()
        self.name = name
        self.password = password
        self.email = email

        api_key = new_api_key()
        while self.__class__.query.filter_by(api_key=api_key).all():
            api_key = new_api_key()
        self.api_key = api_key

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

