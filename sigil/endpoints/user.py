from . import ManagedResource, reqparse
from ..utils import current_user
from ..models import User


class UserDetails(ManagedResource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str)
        args = parser.parse_args()

        if args['username']:
            user = User.by_username(args['username'])
        else:
            user = current_user

        return {'firstname': user.fn,
                'lastname': user.sn,
                'username': user.username,
                'displayname': user.display_name,
                'id': user.id}
