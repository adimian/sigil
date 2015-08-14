import flask_restful as restful

from ..utils import requires_authentication


class ProtectedResource(restful.Resource):
    method_decorators = [requires_authentication]
