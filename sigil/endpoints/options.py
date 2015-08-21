from ..endpoints import AnonymousResource
from flask import current_app as app


class ServerOptions(AnonymousResource):
    def get(self):
        return {'use_totp': app.config['ENABLE_2FA'],
                'auth_token': app.config['SESSION_TOKEN_HEADER']}
