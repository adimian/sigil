from flask_login import login_required

import flask_restful as restful


class ProtectedResource(restful.Resource):
    method_decorators = [login_required]
