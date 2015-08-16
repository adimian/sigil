from . import ManagedResource, reqparse
from ..utils import current_user
from ..models import User


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
