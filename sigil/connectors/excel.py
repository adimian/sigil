import logging
import re

import openpyxl

from ..models import User
import sqlalchemy


logger = logging.getLogger(__name__)


class MissingFieldError(Exception):
    pass


class InvalidEmailError(Exception):
    pass


class DuplicatedUserError(Exception):
    pass


class SheetProcessor(object):

    object_class = None
    mandatory_fields = ()

    def __init__(self, sheet):
        self._headers = None
        self.sheet = sheet

    @property
    def headers(self):
        if self._headers is None:
            top = next(self.sheet.rows)
            self._headers = [str(f.value).strip().lower() for f in top]
        return self._headers

    def cleanup(self, item):
        for key in item:
            cleanup_func = getattr(self, 'cleanup_{}'.format(key), None)
            if cleanup_func:
                item[key] = cleanup_func(item[key])
        return item

    @property
    def data(self):
        self.check()
        names = self.headers
        rows = self.sheet.rows
        next(rows)
        for row in rows:
            yield self.cleanup(dict(zip(names,
                                        [str(c.value).strip() for c in row])))

    def check(self):
        for field in self.mandatory_fields:
            if field not in self.headers:
                msg = 'missing field "{}" in "{}" sheet'.format(field,
                                                                self.sheet.title)
                raise MissingFieldError(msg)

    def read(self):
        NotImplementedError()


class UserProcessor(SheetProcessor):
    object_class = User
    mandatory_fields = ('username', 'email', 'mobile')

    def cleanup_username(self, name):
        if not name:
            raise ValueError('name is required')
        return re.sub('\s', '', str(name).lower())

    def cleanup_mobile(self, mobile):
        return re.sub('[^+0-9]', '', mobile)

    def cleanup_email(self, email):
        if not email:
            raise ValueError('email is required')
        if '@' not in email:
            raise InvalidEmailError('{} is not a valid email'.format(email))
        return email

    def read(self):
        # deactivated
        deactivated = []
        actives = set([x['username'] for x in self.data])
        for user in User.query.all():
            if user.username not in actives:
                deactivated.append(user)

        # created
        added = []
        updated = []
        for item in self.data:
            entity = User.by_username(item['username'])
            if not entity:
                entity = User(username=item['username'],
                              email=item['email'],
                              mobile=item['mobile'])
                added.append(entity)
            else:
                updated.append(entity)

            for key in item:
                setattr(entity, key, item[key])

        return added, updated, deactivated


class ExcelConnector(object):
    def __init__(self, session, user):
        self.session = session
        self.user = user

    def _find_dupe(self, message, users):
        for user in users:
            if user in message:
                return user
        return 'unknown'

    def process_users(self, sheet):
        p = UserProcessor(sheet)
        added, _, deactivated = p.read()

        for user in added:
            self.session.add(user)

        for user in deactivated:
            user.active = False

        try:
            self.session.commit()
        except sqlalchemy.exc.IntegrityError as err:
            dupe_user = self._find_dupe(err.params,
                                        [u.username for u in added])
            raise DuplicatedUserError('{} for {}'.format(str(err.orig),
                                                         dupe_user))

        for user in added:
            user.generate_token()

    def process_groups(self, sheet):
        pass

    def process_teams(self, sheet):
        pass

    def process(self, fobj):
        wb = openpyxl.load_workbook(fobj.stream, read_only=True,
                                    use_iterators=True,
                                    data_only=True)

        sheets = set(wb.sheetnames)

        # objects
        for sheetname in ('users', 'groups', 'teams'):
            if sheetname in sheets:
                f_name = 'process_{}'.format(sheetname)
                f = getattr(self, f_name)
                if not f:
                    raise Exception('{} not found'.format(f_name))
                logger.info('handling {} change'.format(sheetname))
                f(wb[sheetname])
                logger.info('done handling {} change'.format(sheetname))
                sheets.remove(sheetname)

        # permissions
        for context in sheets:
            logger.info('handling permission change for {}'.format(context))

        try:
            self.session.commit()
        except sqlalchemy.exc.IntegrityError as err:
            raise DuplicatedUserError(str(err.orig))
