import flask_restful as restful
from flask_restful import reqparse

from ..utils import requires_authentication, requires_anonymous, self_or_manager


class ProtectedResource(restful.Resource):
    method_decorators = [requires_authentication]


class ManagedResource(restful.Resource):
    method_decorators = [self_or_manager]


class AnonymousResource(restful.Resource):
    method_decorators = [requires_anonymous]
