import json

from flask import abort
import sqlalchemy

from . import ManagedResource, reqparse
from ..api import db
from ..models import AppContext, User, Need
from ..utils import current_user


def get_target_user():
    parser = reqparse.RequestParser()
    parser.add_argument('username', type=str)
    args = parser.parse_args()

    if args['username']:
        user = User.by_username(args['username'])
    else:
        user = current_user
    return user


class UserDetails(ManagedResource):
    def get(self):
        user = get_target_user()
        return {'firstname': user.fn,
                'lastname': user.sn,
                'username': user.username,
                'displayname': user.display_name,
                'id': user.id}


class UserPermissions(ManagedResource):
    def get(self):
        user = get_target_user()
        parser = reqparse.RequestParser()
        parser.add_argument('context', type=str, required=True)
        args = parser.parse_args()
        return {'provides': user.provides(args['context'])}

    def post(self):
        user = get_target_user()
        parser = reqparse.RequestParser()
        parser.add_argument('context', type=str, required=True)
        parser.add_argument('needs', type=str, required=True)
        args = parser.parse_args()

        try:
            ctx = AppContext.query.filter_by(name=args['context']).one()
        except sqlalchemy.orm.exc.NoResultFound as err:
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
            user.permissions.append(need)

        db.session.commit()

        return {'provides': user.provides(args['context'])}
