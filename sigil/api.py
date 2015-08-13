import logging
import sys

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

import flask_restful as restful

from .conf import configure


app = Flask('sigil')
configure(app)

if app.config['DEBUG']:
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


def setup_endpoints():
    logger.info('setting up endpoints')
    from .endpoints.register import Register

    api = restful.Api(app)
    api.add_resource(Register, '/<string:persona_class>/register')
    logger.info('endpoints ready')

setup_endpoints()
