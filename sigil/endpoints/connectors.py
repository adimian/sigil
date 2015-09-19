import os
import tempfile

from flask import abort, send_from_directory
from flask_principal import Permission
from flask_restful import reqparse
import werkzeug

import os.path as osp

from . import ProtectedResource, AnonymousResource
from ..api import db, app
from ..connectors.excel import (ExcelConnector, MissingFieldError,
                                InvalidEmailError, DuplicatedUserError,
                                ExcelExporter)
from ..utils import current_user, generate_token, read_token, md5


DIRECTORY = tempfile.gettempdir()


class ExcelImport(ProtectedResource):
    def post(self):
        with Permission(('users', 'write')).require(403):
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
        with Permission(('users', 'read')).require(403):
            fd, filename = tempfile.mkstemp(suffix='.xlsx', prefix='sigil_export_',
                                            dir=DIRECTORY)
            os.close(fd)
            ExcelExporter(db.session, current_user).export(filename)
            ex_filename = osp.basename(filename)
            token = generate_token((ex_filename, md5(filename)),
                                   app.config['FILE_DOWNLOAD_SALT'])
            return {'token': token}


class ExcelDownload(AnonymousResource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('token', type=str, required=True)
        args = parser.parse_args()
        filename, _ = read_token(args['token'],
                                 app.config['FILE_DOWNLOAD_SALT'])
        return send_from_directory(directory=DIRECTORY,
                                   filename=filename,
                                   as_attachment=True,
                                   attachment_filename=osp.basename(filename))
