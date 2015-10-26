import json

import os.path as osp
from sigil.models import User, VirtualGroup
import openpyxl
import os
import sys


data_dir = osp.join(osp.dirname(__file__), 'data')


def test_import_excel(client):
    import_file = osp.join(data_dir, 'sigil.xlsx')
    rv = client.post('/import/excel', data={'file': open(import_file, 'rb')},
                     headers=client._auth_headers)

    assert rv.status_code == 200, str(rv.data)

    assert User.by_username('eric').id
    assert VirtualGroup.by_name('jabber').id

    assert sorted([g.name for g in
                   User.by_username('eric').groups]) == sorted(['jabber',
                                                                'jenkins'])
    assert len(User.by_username('eric').extra_fields.all()) == 2
    assert User.by_username('eric').company == 'Adimian'
    assert User.by_username('eric').department == 'Belgium'


def test_import_excel_with_dupes(client):
    import_file = osp.join(data_dir, 'sigil_dupes.xlsx')
    rv = client.post('/import/excel', data={'file': open(import_file, 'rb')},
                     headers=client._auth_headers)

    assert rv.status_code == 409, str(rv.data)


def test_import_excel_with_illigal_fields(client):
    import_file = osp.join(data_dir, 'sigil_illigal_fields.xlsx')
    rv = client.post('/import/excel', data={'file': open(import_file, 'rb')},
                     headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)

    user = User.by_username('eric')
    assert not user.totp_secret == 'OVERRIDE'
    assert not hasattr(user, 'does_not_exist')


def test_export_excel(client):
    import_file = osp.join(data_dir, 'sigil.xlsx')
    rv = client.post('/import/excel', data={'file': open(import_file, 'rb')},
                     headers=client._auth_headers)

    assert rv.status_code == 200, str(rv.data)

    rv = client.get('/export/excel', headers=client._auth_headers)
    assert rv.status_code == 200, str(rv.data)
    data = json.loads(rv.data.decode('utf-8'))
    assert data['token']

    rv = client.get('/download/excel',
                    data={'token': data['token']})
    assert rv.status_code == 200, str(rv.data)

    wb = openpyxl.load_workbook(rv.response.file)
    check_up_row = None
    for row in wb['users'].rows:
        if 'eric' in [cell.value for cell in row]:
            check_up_row = row
    assert check_up_row

    assert wb['groups']['A2'].value in ('eric', 'maarten',
                                        'xme', 'alice', 'bernard')

    assert check_up_row[5].value in ('Belgium', 'Adimian')
    assert check_up_row[6].value in ('Belgium', 'Adimian')
