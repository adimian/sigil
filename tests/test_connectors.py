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


def test_import_excel_with_dupes(client):
    import_file = osp.join(data_dir, 'sigil_dupes.xlsx')
    rv = client.post('/import/excel', data={'file': open(import_file, 'rb')},
                     headers=client._auth_headers)

    assert rv.status_code == 409, str(rv.data)


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

    if sys.platform == 'darwin':
        f = rv.response.file
        os.system('open {}'.format(f.name))
    wb = openpyxl.load_workbook(rv.response.file)
    assert wb['users']['A2'].value in ('eric', 'maarten',
                                       'xme', 'alice', 'bernard')

    assert wb['groups']['A2'].value in ('eric', 'maarten',
                                        'xme', 'alice', 'bernard')
