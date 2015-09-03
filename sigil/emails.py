from flask_mail import Message

from .api import app, mail
from .signals import user_registered


def setup_emails():
    @user_registered.connect_via(app)
    def send_register_email(sender, user, token):
        msg = Message("Welcome to Sigil",
                      recipients=[user.email])
        msg.html = "Your token is {}".format(token)
        mail.send(msg)
