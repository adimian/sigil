from itertools import product
import json

from flask import abort
from flask_principal import Permission
import sqlalchemy

from . import ManagedResource, reqparse, AnonymousResource
from ..api import db, app
from ..models import AppContext, Need
from ..utils import current_user, generate_token, read_token, md5

MANDATORY_NEEDS = ('permissions',)


class ApplicationContext(ManagedResource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        args = parser.parse_args()

        if Permission(('appcontexts', 'write')).can():
            ctx = AppContext(args['name'])
            db.session.add(ctx)
            # give default permissions for the new app to the creator
            for need in product(MANDATORY_NEEDS,
                                ('read', 'write')):
                need = Need(ctx, *need)
                db.session.add(need)
                current_user.permissions.append(need)
            db.session.commit()

            return {'application-key': generate_token([ctx.id, md5(ctx.name)],
                                                      salt=app.config['APPLICATION_KEY_SALT'])}
        else:
            abort(403)


class ApplicationNeeds(AnonymousResource):

    def get_app_context(self):
        parser = reqparse.RequestParser()
        parser.add_argument('application-key', type=str, required=True)
        args = parser.parse_args()
        context, _ = read_token(args['application-key'],
                                salt=app.config['APPLICATION_KEY_SALT'])
        try:
            ctx = AppContext.query.filter_by(id=context).one()
        except sqlalchemy.orm.exc.NoResultFound as err:
            abort(400, 'application not found')
        return ctx

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('needs', type=str, required=True)
        args = parser.parse_args()

        ctx = self.get_app_context()

        for need in set(map(tuple, json.loads(args['needs']))):
            db.session.add(Need(ctx, *need))
        db.session.commit()

        return {'needs': ctx.show()}

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('needs', type=str, required=True)
        args = parser.parse_args()

        ctx = self.get_app_context()

        removed_needs = set(map(tuple, json.loads(args['needs'])))
        for need in Need.query.filter_by(app_context=ctx).all():
            if need.as_tuple() in removed_needs:
                db.session.delete(need)
        db.session.commit()

        return {'needs': ctx.show()}
