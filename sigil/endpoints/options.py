from flask import current_app as app

from .. import __version__
from ..endpoints import AnonymousResource


class ServerOptions(AnonymousResource):
    def get(self):
        return {'use_totp': app.config['ENABLE_2FA'],
                'auth_token': app.config['SESSION_TOKEN_HEADER'],
                'version': __version__}
