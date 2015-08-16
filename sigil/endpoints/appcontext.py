from flask_principal import Permission
from flask import abort

from . import ManagedResource, reqparse
from ..models import AppContext
from ..api import db


class ApplicationContext(ManagedResource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        args = parser.parse_args()

        if Permission(('appcontexts', 'write')).can():
            db.session.add(AppContext(args['name']))
            db.session.commit()
        else:
            abort(403)
