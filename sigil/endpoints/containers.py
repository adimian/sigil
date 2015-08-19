import json

from flask_principal import Permission
from flask_restful import reqparse

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
            db.session.commit()

            return {'name': group.name,
                    'active': group.active}


class VirtualGroupMembers(ProtectedResource):
    def post(self):
        with Permission(('groups', 'write')).require():
            parser = reqparse.RequestParser()
            parser.add_argument('name', type=str, required=True)
            parser.add_argument('usernames', type=str, required=True)
            args = parser.parse_args()

            group = db.session.query(VirtualGroup).filter_by(name=args['name']).one()

            for username in set(json.loads(args['usernames'])):
                user = db.session.query(User).filter_by(username=username).one()
                group.members.append(user)

            db.session.commit()
