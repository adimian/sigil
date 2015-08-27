from flask import abort
from flask_restful import reqparse
import werkzeug

from . import ProtectedResource
from ..api import db
from ..connectors.excel import (ExcelConnector, MissingFieldError,
                                InvalidEmailError)
from ..utils import current_user
import sqlalchemy


class ExcelImport(ProtectedResource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file', type=werkzeug.datastructures.FileStorage,
                            location='files', required=True)
        args = parser.parse_args()
        connector = ExcelConnector(db.session, current_user)
        try:
            return connector.process(args['file'])
        except (MissingFieldError, InvalidEmailError) as err:
            abort(400, str(err))
        except sqlalchemy.exc.IntegrityError as err:
            abort(409, 'duplicate information')

