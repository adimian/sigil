import json

from flask import abort
from flask_principal import Permission
from flask_restful import reqparse
import sqlalchemy

from . import ProtectedResource
from ..api import db
from ..models import VirtualGroup, User, UserTeam
from .permissions import ResourcePermissions


class ContainerResource(ProtectedResource):

    def get_group(self):
        with Permission(self.permission_type).require(403):
            parser = reqparse.RequestParser()
            parser.add_argument('name', type=str, required=True)
            args = parser.parse_args()
            try:
                return db.session.query(self.container_type).filter_by(name=args['name']).one()
            except sqlalchemy.orm.exc.NoResultFound:
                abort(404, '{} not found'.format(self.resource_type))

    def get(self):
        with Permission(self.permission_type).require(403):
            response = []
            for group in db.session.query(self.container_type).all():
                response.append({'id': group.id,
                                 'name': group.name,
                                 'active': group.active})
            return {'{}s'.format(self.resource_type): response}

    def patch(self):
        group = self.get_group()
        parser = reqparse.RequestParser()
        parser.add_argument('active', type=str, required=True)
        args = parser.parse_args()
        group.active = args['active'] == 'true'
        db.session.commit()

    def post(self):
        with Permission(self.permission_type).require(403):
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
        with Permission(self.permission_type).require(403):
            parser = reqparse.RequestParser()
            parser.add_argument('name', type=str, required=True)
            args = parser.parse_args()
            try:
                return db.session.query(self.container_type).filter_by(name=args['name']).one()
            except sqlalchemy.orm.exc.NoResultFound:
                abort(404, '{} not found'.format(self.resource_type))

    def post(self):
        self.update_members(mode='add')

    def delete(self):
        self.update_members(mode='delete')

    def get(self):
        group = self.get_group()
        return {'users': [u.public() for u in group.members],
                'active': group.active}

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
                if user not in group.members:
                    group.members.append(user)
            elif mode == 'delete':
                if user in group.members:
                    group.members.remove(user)
        db.session.commit()


class VirtualGroupResource(ContainerResource):
    resource_type = 'group'
    container_type = VirtualGroup
    permission_type = ('groups', 'write')


class UserTeamResource(ContainerResource):
    resource_type = 'team'
    container_type = UserTeam
    permission_type = ('teams', 'write')


class VirtualGroupMembers(ContainerMembers):
    resource_type = 'group'
    container_type = VirtualGroup
    permission_type = ('groups', 'write')


class UserTeamMembers(ContainerMembers):
    resource_type = 'group'
    container_type = UserTeam
    permission_type = ('teams', 'write')


def get_target_team():
    parser = reqparse.RequestParser()
    parser.add_argument('name', type=str, required=True)
    args = parser.parse_args()

    team = UserTeam.by_name(args['name'])
    if team is None:
        abort(404, 'unknown team {}'.format(args['name']))
    return team


class UserTeamPermissions(ResourcePermissions):

    def get_target(self):
        return get_target_team()
