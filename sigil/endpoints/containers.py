import json

from flask import abort
from flask_principal import Permission
from flask_restful import reqparse
import sqlalchemy

from . import ProtectedResource
from ..api import db
from ..models import VirtualGroup, User


class VirtualGroupResource(ProtectedResource):
    def post(self):
        with Permission(('groups', 'write')).require():
            parser = reqparse.RequestParser()
            parser.add_argument('name', type=str, required=True)
            args = parser.parse_args()
            group = VirtualGroup(name=args['name'])

            db.session.add(group)
            try:
                db.session.commit()
            except sqlalchemy.exc.IntegrityError:
                abort(409, 'group already exists')

            return {'name': group.name,
                    'active': group.active}


class VirtualGroupMembers(ProtectedResource):
    def get_group(self):
        with Permission(('groups', 'write')).require():
            parser = reqparse.RequestParser()
            parser.add_argument('name', type=str, required=True)
            args = parser.parse_args()
            try:
                return db.session.query(VirtualGroup).filter_by(name=args['name']).one()
            except sqlalchemy.orm.exc.NoResultFound:
                abort(404, 'group not found')

    def post(self):
        self.update_members(mode='add')

    def delete(self):
        self.update_members(mode='delete')

    def update_members(self, mode):
        parser = reqparse.RequestParser()
        parser.add_argument('usernames', type=str, required=True)
        args = parser.parse_args()

        group = self.get_group()
        for username in set(json.loads(args['usernames'])):
            try:
                user = db.session.query(User).filter_by(username=username).one()
            except sqlalchemy.orm.exc.NoResultFound:
                abort(404, 'user {} not found'.format(username))

            if mode == 'add':
                group.members.append(user)
            elif mode == 'delete':
                group.members.remove(user)
        db.session.commit()
