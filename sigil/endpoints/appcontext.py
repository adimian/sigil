from flask_principal import Permission
from flask import abort
from itertools import product

from . import ManagedResource, reqparse
from ..models import AppContext, Need
from ..api import db
from ..utils import current_user


class ApplicationContext(ManagedResource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        args = parser.parse_args()

        if Permission(('appcontexts', 'write')).can():
            ctx = AppContext(args['name'])
            db.session.add(ctx)
            # give default permissions for the new app to the creator
            for need in product(('permissions',),
                                ('read', 'write')):
                need = Need(ctx, *need)
                db.session.add(need)
                current_user.permissions.append(need)
            db.session.commit()
        else:
            abort(403)
