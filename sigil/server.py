from flask_script import Manager, Server, prompt_pass, Shell
import logging

from sigil.api import app, db, setup_endpoints
from sigil.emails import setup_emails
from sigil.models import User
from sigil.permissions import setup_default_permissions
from sigil.ldap import update_ldap


setup_endpoints()
setup_emails()


@app.before_first_request
def create_db():
    db.create_all()
    setup_default_permissions()


class DebugShell(Shell):
    def run(self, *args, **kwargs):
        logging.basicConfig(level=logging.DEBUG)
        return Shell.run(self, *args, **kwargs)


manager = Manager(app)
manager.add_command("runserver", Server(host=app.config['HOST'],
                                        port=app.config['PORT']))
manager.add_command('shell', DebugShell())


if app.config['DEBUG']:
    @manager.command
    def reset():
        print('resetting the database')
        db.drop_all()
        db.create_all()
        setup_default_permissions()
        print('reset done')

    @manager.command
    def superuser(username, email):
        user = User(username, email)
        user.active = True
        user.must_change_password = False
        user.password = prompt_pass('password')
        db.session.add(user)
        db.session.commit()
        print('user {} added with id {}'.format(user.username, user.id))


@manager.command
def force_ldap_update():
    logging.basicConfig(level=logging.DEBUG)
    update_ldap()


if __name__ == "__main__":
    manager.run()
