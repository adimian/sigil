from os import environ


def configure(app):
    config = app.config

    def set_default(key, value):
        config[key] = environ.get(key, value)

    set_default('DEBUG', True)
    set_default('SECRET_KEY', 'secret-key')
    set_default('REGISTER_USER_TOKEN_SALT', 'register-salt')
    set_default('SENTRY_DSN', 'https://2d79967d03cb4cec85988bc42dd6bbc8:0e1a27aeb00144718d92627185b2154c@sentry.adimian.com/9')
