from os import environ


def configure(app):
    config = app.config

    def set_default(key, value):
        v = environ.get(key, value)
        try:
            v = int(v)
        except:
            pass
        if isinstance(v, str):
            if v.lower() in ('false', 'no'):
                v = False
            elif v.lower() in('true', 'yes'):
                v = True
        config[key] = v

    set_default('DEBUG', False)
    set_default('HOST', '0.0.0.0')
    set_default('PORT', 5000)
    set_default('API_URL_PREFIX', '')
    set_default('SQLALCHEMY_DATABASE_URI', 'sqlite:///')
    set_default('SECRET_KEY', 'secret-key')
    set_default('UPDATE_PASSWORD_TOKEN_SALT', 'register-salt')
    set_default('SENTRY_DSN', '')
    set_default('SESSION_TOKEN_MAX_AGE', 86400)  # 1 day
    set_default('SESSION_TOKEN_SALT', 'session-salt')
    set_default('APPLICATION_KEY_SALT', 'application-key-salt')
    set_default('SESSION_TOKEN_HEADER', 'Sigil-Token')
    set_default('ROOT_APP_CTX', 'sigil')
    set_default('AUTO_ACTIVATE_NEW_USER', True)

    # 2FA
    set_default('ENABLE_2FA', False)
    set_default('TOTP_MAX_TIME_STEPS', 20)
    set_default('TOTP_TIME_STEP', 30)
    set_default('TOTP_EXPIRATION', 30 * 86400)  # 1 month
    set_default('TOTP_DOMAIN', 'docker.dev')


