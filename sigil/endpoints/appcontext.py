from itertools import product
import json
import logging
import os

from flask import abort
from flask_principal import Permission
import sqlalchemy

from . import reqparse, AnonymousResource, ProtectedResource
from ..api import db, app
from ..models import AppContext, Need
from ..permissions import APP_MANDATORY_NEEDS
from ..utils import current_user, generate_token, read_token, md5


logger = logging.getLogger(__name__)


class ApplicationContext(ProtectedResource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        args = parser.parse_args()

        ctx = AppContext.by_name(args['name'])
        if ctx is not None:
            return {'needs': ctx.declared_needs()}
        else:
            apps = []
            if Permission(('appcontexts', 'read')).can():
                for ctx in db.session.query(AppContext).all():
                    apps.append({'id': ctx.id,
                                 'name': ctx.name,
                                 'needs': ctx.declared_needs()})
            return {'apps': apps}

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        args = parser.parse_args()

        if Permission(('appcontexts', 'write')).can():
            ctx = AppContext(args['name'])
            db.session.add(ctx)
            # give default permissions for the new app to the creator
            for need in product(APP_MANDATORY_NEEDS,
                                ('read', 'write')):
                need = Need(ctx, *need)
                db.session.add(need)
                current_user.permissions.append(need)
            try:
                db.session.commit()
            except sqlalchemy.exc.IntegrityError:
                db.session.rollback()
                abort(409, 'an application with the same name already exists')

            app_key = generate_token([ctx.id, md5(ctx.name)],
                                     salt=app.config['APPLICATION_KEY_SALT'])

            if app.config['APP_KEYS_FOLDER']:
                keyfile = os.path.join(app.config['APP_KEYS_FOLDER'],
                                       '{}.appkey'.format(ctx.name))
                with open(keyfile, 'w') as f:
                    f.write(app_key)

            return {'application-key': app_key}
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
            if not Need.by_tuple(ctx, need):
                db.session.add(Need(ctx, *need))
            else:
                logger.warning('ignoring add of {} in context {}'
                               'because it already exists'.format(repr(need),
                                                                  ctx.name))
        db.session.commit()

        return {'needs': ctx.declared_needs()}

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('needs', type=str, required=True)
        args = parser.parse_args()

        ctx = self.get_app_context()

        removed_needs = set(map(tuple, json.loads(args['needs'])))
        for need in Need.query.filter_by(app_context=ctx).all():
            nat = need.as_tuple()
            if nat in removed_needs:
                if nat[0] not in APP_MANDATORY_NEEDS:
                    db.session.delete(need)
        db.session.commit()

        return {'needs': ctx.declared_needs()}
