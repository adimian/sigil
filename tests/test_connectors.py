import json

import os.path as osp
from sigil.models import User


data_dir = osp.join(osp.dirname(__file__), 'data')


def test_import_excel(client):
    import_file = osp.join(data_dir, 'sigil.xlsx')
    rv = client.post('/import/excel', data={'file': open(import_file, 'rb')},
                     headers=client._auth_headers)

    assert rv.status_code == 200, str(rv.data)

    assert User.by_username('eric').id
