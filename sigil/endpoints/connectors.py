from flask import abort, send_file
from flask_restful import reqparse
import werkzeug

import os.path as osp

from . import ProtectedResource
from ..api import db
from ..connectors.excel import (ExcelConnector, MissingFieldError,
                                InvalidEmailError, DuplicatedUserError,
                                ExcelExporter)
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


class ExcelExport(ProtectedResource):
    def get(self):
        filename = ExcelExporter(db.session, current_user).export()
        return send_file(filename,
                         as_attachment=True,
                         attachment_filename=osp.basename(filename))
