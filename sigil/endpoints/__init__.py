import flask_restful as restful

from ..utils import requires_authentication, requires_anonymous


class ProtectedResource(restful.Resource):
    method_decorators = [requires_authentication]


class AnonymousResource(restful.Resource):
    method_decorators = [requires_anonymous]
