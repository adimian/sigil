import json

from flask import abort
from flask_principal import Permission
from flask_restful import reqparse
import sqlalchemy

from . import ProtectedResource
from ..api import db
from ..models import VirtualGroup, User, UserTeam


class ContainerResource(ProtectedResource):

    def post(self):
        with Permission(('groups', 'write')).require():
            parser = reqparse.RequestParser()
            parser.add_argument('name', type=str, required=True)
            args = parser.parse_args()
            group = self.container_type(name=args['name'])

            db.session.add(group)
            try:
                db.session.commit()
            except sqlalchemy.exc.IntegrityError:
                abort(409, '{} already exists'.format(args['name']))

            return {'name': group.name,
                    'active': group.active}


class ContainerMembers(ProtectedResource):

    def get_group(self):
        with Permission(self.permission_type).require():
            parser = reqparse.RequestParser()
            parser.add_argument('name', type=str, required=True)
            args = parser.parse_args()
            try:
                return db.session.query(self.container_type).filter_by(name=args['name']).one()
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


class VirtualGroupResource(ContainerResource):
    container_type = VirtualGroup


class UserTeamResource(ContainerResource):
    container_type = UserTeam


class VirtualGroupMembers(ContainerMembers):
    container_type = VirtualGroup
    permission_type = ('groups', 'write')


class UserTeamMembers(ContainerMembers):
    container_type = UserTeam
    permission_type = ('teams', 'write')
