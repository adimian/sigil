from os import environ


def configure(app):
    config = app.config

    def set_default(key, value):
        config[key] = environ.get(key, value)

    set_default('DEBUG', False)
    set_default('HOST', '0.0.0.0')
    set_default('PORT', 5000)
    set_default('SQLALCHEMY_DATABASE_URI', 'sqlite:///')
    set_default('SECRET_KEY', 'secret-key')
    set_default('REGISTER_USER_TOKEN_SALT', 'register-salt')
    set_default('SENTRY_DSN', 'https://2d79967d03cb4cec85988bc42dd6bbc8:0e1a27aeb00144718d92627185b2154c@sentry.adimian.com/9')
    set_default('SESSION_TOKEN_MAX_AGE', 86400)  # 1 day
    set_default('SESSION_TOKEN_SALT', 'session-salt')
    set_default('APPLICATION_KEY_SALT', 'application-key-salt')
    set_default('SESSION_TOKEN_HEADER', 'Sigil-Token')
    set_default('ROOT_APP_CTX', 'sigil')
