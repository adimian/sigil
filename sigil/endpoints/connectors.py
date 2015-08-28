from flask import abort
from flask_restful import reqparse
import werkzeug

from . import ProtectedResource
from ..api import db
from ..connectors.excel import (ExcelConnector, MissingFieldError,
                                InvalidEmailError, DuplicatedUserError)
from ..utils import current_user


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
        except DuplicatedUserError as err:
            abort(409, str(err))

