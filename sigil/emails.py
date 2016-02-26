import os
from flask_mail import Message
from .utils import current_user

from .api import app, mail, logger
from .signals import user_registered, user_request_password_recovery

from jinja2 import Environment, PackageLoader, FileSystemLoader
from jinja2.exceptions import TemplateNotFound


def get_template(template_name, default_template_name):
    package_env = Environment(loader=PackageLoader('sigil', 'templates'))
    template_folder = app.config['MAIL_TEMPLATE_FOLDER']
    filesystem_env = Environment(loader=FileSystemLoader(template_folder))
    try:
        template = filesystem_env.get_template(template_name)
    except TemplateNotFound:
        message = ("Could not find template '%s' in '%s', "
                   "defaulting to internal template folder")
        args = (template_name, app.config['MAIL_TEMPLATE_FOLDER'])
        logger.info(message % args)
        template = package_env.get_template(default_template_name)
    return template


def setup_emails():
    @user_registered.connect_via(app)
    def send_register_email(sender, user, token):
        msg = Message("New account created for {}".format(app.config['APPLICATION_NAME']),
                      recipients=[user.email])
        template_name = app.config['MAIL_TEMPLATES']['REGISTER']
        template = get_template(template_name, "email_register.html")

        base_url = '/'.join((app.config['UI_BASE_URL'],
                            'validate.html'))

        url = '{}?token={}'.format(base_url, token)
        msg.html = template.render(creator=current_user.display_name,
                                   user=user.username,
                                   app_name=app.config['APPLICATION_NAME'],
                                   url=url)
        if app.config['DEBUG'] and not app.config['TESTING']:
            print(msg.subject)
            print(msg.html)
        else:
            mail.send(msg)

    @user_request_password_recovery.connect_via(app)
    def send_recover_email(sender, user, token):
        title = "{}: password recovery for {}".format(app.config['APPLICATION_NAME'],
                                                      user.username)
        msg = Message(title, recipients=[user.email])
        template_name = app.config['MAIL_TEMPLATES']['RECOVER']
        template = get_template(template_name, "email_recover.html")

        base_url = '/'.join((app.config['UI_BASE_URL'],
                            'validate.html'))

        url = '{}?token={}'.format(base_url, token)
        msg.html = template.render(user=user.display_name,
                                   app_name=app.config['APPLICATION_NAME'],
                                   url=url)
        if app.config['DEBUG'] and not app.config['TESTING']:
            print(msg.subject)
            print(msg.html)
        else:
            mail.send(msg)
