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
    set_default('STANDALONE', False)
    set_default('SERVER_NAME', None)
    set_default('ERROR_404_HELP', False)
    set_default('APPLICATION_NAME', 'Sigil')
    set_default('UI_BASE_URL', 'http://docker.dev/sigil')
    set_default('API_URL_PREFIX', '')
    set_default('SERVE_STATIC', False)
    set_default('UI_URL_PREFIX', '')
    set_default('SQLALCHEMY_DATABASE_URI', 'sqlite:///')
    set_default('SECRET_KEY', 'secret-key')
    set_default('UPDATE_PASSWORD_TOKEN_SALT', 'register-salt')
    set_default('SENTRY_DSN', '')
    set_default('SESSION_TOKEN_MAX_AGE', 86400)  # 1 day
    set_default('SESSION_TOKEN_SALT', 'session-salt')
    set_default('APPLICATION_KEY_SALT', 'application-key-salt')
    set_default('FILE_DOWNLOAD_SALT', 'file-download')
    set_default('SESSION_TOKEN_HEADER', 'Sigil-Token')
    set_default('ROOT_APP_CTX', 'sigil')
    set_default('AUTO_ACTIVATE_NEW_USER', True)
    set_default('EXTRA_FIELDS', 'department,company')

    # mail
    set_default('MAIL_SUPPRESS_SEND', True)
    set_default('MAIL_SERVER', '')
    set_default('MAIL_USERNAME', '')
    set_default('MAIL_PORT', '587')
    set_default('MAIL_USE_TLS', True)
    set_default('MAIL_PASSWORD', '')
    set_default('MAIL_DEFAULT_SENDER', 'sigil@local')
    set_default('MAIL_TEMPLATE_FOLDER', '')
    set_default('MAIL_TEMPLATES', {'REGISTER': 'email_register.html',
                                   'RECOVER': 'email_recover.html'})

    # 2FA
    set_default('ENABLE_2FA', False)
    set_default('TOTP_MAX_TIME_STEPS', 20)
    set_default('TOTP_TIME_STEP', 30)
    set_default('TOTP_EXPIRATION', 30 * 86400)  # 1 month
    set_default('TOTP_DOMAIN', 'docker.dev')

    # OVH (SMS)
    set_default('OVH_ENDPOINT', '')
    set_default('OVH_APPLICATION_KEY', '')
    set_default('OVH_APPLICATION_SECRET', '')
    set_default('OVH_CONSUMER_KEY', '')
    set_default('OVH_SMS_SENDER', '')
    set_default('OVH_SMS_SERVICE', '')

    # LDAP
    set_default('LDAP_HOST', 'docker.dev')
    set_default('LDAP_PORT', 389)
    set_default('LDAP_ROOT_DN', 'dc=mycorp,dc=com')
    set_default('LDAP_BIND_DN', 'cn=admin,dc=mycorp,dc=com')
    set_default('LDAP_BIND_PASSWORD', 's3cr3tpassw0rd')
    set_default('LDAP_USERS_OU', 'Users')
    set_default('LDAP_GROUPS_OU', 'Groups')
    set_default('LDAP_AUTO_UPDATE', False)

