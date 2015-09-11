from flask_mail import Message
from .utils import current_user

from .api import app, mail
from .signals import user_registered

from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('sigil', 'templates'))


def setup_emails():
    @user_registered.connect_via(app)
    def send_register_email(sender, user, token):
        msg = Message("Welcome to Sigil",
                      recipients=[user.email])
        template = env.get_template('email_register.html')

        base_url = '/'.join((app.config['UI_BASE_URL'],
                            'validate.html'))

        msg.html = template.render(creator=current_user,
                                   token=token,
                                   user=user,
                                   validate_url=base_url)
        if app.config['DEBUG'] and not app.config['TESTING']:
            print(msg.html)
        else:
            mail.send(msg)
