from flask_restful import reqparse

from . import ProtectedResource
from ..models import VirtualGroup
from ..api import db


class VirtualGroupResource(ProtectedResource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        args = parser.parse_args()
        group = VirtualGroup(name=args['name'])

        db.session.add(group)
        db.session.commit()

        return {'name': group.name,
                'active': group.active}
