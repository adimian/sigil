import hmac
import time
import uuid

from flask import current_app as app
import pyotp
import qrcode
from six import BytesIO


def new_user_secret():
    return pyotp.random_base32()


def build_uri(user, domain, user_secret):
    totp = pyotp.TOTP(user_secret)
    return totp.provisioning_uri('%s@%s' % (user, domain))


def get_code(user_secret):
    return pyotp.TOTP(user_secret).now()


def check_code(user_secret, code):
    totp = pyotp.TOTP(user_secret)

    # Check nearly expired codes
    now = int(time.time())
    for i in range(app.config['TOTP_MAX_TIME_STEPS']):
        for_time = now - (i * app.config['TOTP_TIME_STEP'])
        try:
            succes = totp.verify(code, for_time=for_time)
        except TypeError:  # Raised when code is too short
            return False
        if succes:
            return True
    return False


def ascii_qr_code(uri, invert=False):
    qr = qrcode.QRCode()
    out = BytesIO()
    qr.add_data(uri)
    qr.print_ascii(out=out, invert=invert)
    res = out.getvalue()
    res = '\n'.join(l.rstrip() for l in res.splitlines() if l)
    out.close()
    return res


def qr_code_for_user(user):
    uri = build_uri(user=user.username,
                    domain=app.config['TOTP_DOMAIN'],
                    user_secret=user.totp_secret)
    return ascii_qr_code(uri, invert=False)
