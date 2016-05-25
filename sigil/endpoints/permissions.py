import json
import logging

from flask import abort
import sqlalchemy

from . import ManagedResource, reqparse
from ..api import db
from ..models import AppContext, Need


logger = logging.getLogger(__name__)


class ResourcePermissions(ManagedResource):

    def get_target(self):
        raise NotImplementedError('you need to return the target object here')

    def options(self):
        target = self.get_target()
        response = {}
        for context in db.session.query(AppContext).all():
            response[context.name] = target.permission_catalog(context.name)
        return response

    def get(self):
        target = self.get_target()
        parser = reqparse.RequestParser()
        parser.add_argument('context', type=str, required=True)
        args = parser.parse_args()
        return {'provides': target.provides(args['context'])}

    def update_permissions(self, mode):
        target = self.get_target()
        parser = reqparse.RequestParser()
        parser.add_argument('context', type=str, required=True)
        parser.add_argument('needs', type=str, required=True)
        args = parser.parse_args()

        try:
            ctx = AppContext.query.filter_by(name=args['context']).one()
        except sqlalchemy.orm.exc.NoResultFound:
            abort(400, 'application not found')

        request_needs = set(map(tuple, json.loads(args['needs'])))
        selected_needs = []
        for need in Need.query.filter_by(app_context=ctx).all():
            nat = need.as_tuple()
            if nat in request_needs:
                selected_needs.append(need)
                request_needs.remove(nat)

        if request_needs:
            abort(400,
                  'permissions {} were not found'.format(repr(request_needs)))

        for need in selected_needs:
            if mode == 'add':
                if need not in target.permissions:
                    logger.debug('adding {}, was not in {}'.format(need, target.permissions))
                    target.permissions.append(need)
                else:
                    logger.debug('asked to add {}, but is already there, ignoring'.format(need))
            elif mode == 'delete':
                if need in target.permissions:
                    logger.debug('removing {}, was in {}'.format(need, target.permissions))
                    target.permissions.remove(need)
                else:
                    logger.debug('asked to remove {}, but is not there, ignoring'.format(need))

        db.session.commit()

        return {'provides': target.provides(args['context'])}

    def post(self):
        return self.update_permissions(mode='add')

    def delete(self):
        return self.update_permissions(mode='delete')
