import logging

from flask_alembic.cli.script import manager as alembic_manager
from flask_script import Manager, prompt_pass

from sigil.api import app, db, setup_endpoints, alembic
from sigil.emails import setup_emails
from sigil.ldap import update_ldap
from sigil.models import User
from sigil.permissions import setup_default_permissions


setup_endpoints()
setup_emails()

manager = Manager(app)

manager.add_command('db', alembic_manager)


@manager.command
def superuser(username, email):
    user = User(username, email)
    user.active = True
    user.password = prompt_pass('password')
    db.session.add(user)
    db.session.commit()
    print('user {} added with id {}'.format(user.username, user.id))


@manager.command
def runserver():
    if app.config['DEBUG'] and not app.config['STANDALONE']:
        app.run(host=app.config['HOST'],
                port=app.config['PORT'],
                debug=app.config['DEBUG'])
    else:
        from tornado.wsgi import WSGIContainer
        from tornado.httpserver import HTTPServer
        from tornado.ioloop import IOLoop

        http_server = HTTPServer(WSGIContainer(app))
        http_server.listen(app.config['PORT'], address=app.config['HOST'])
        IOLoop.instance().start()


@manager.command
def init():
    logging.basicConfig(level=logging.INFO)
    alembic.upgrade()
    setup_default_permissions()

if app.config['DEBUG']:
    logging.basicConfig(level=logging.DEBUG)

    @manager.command
    def reset():
        print('resetting the database')
        db.drop_all()
        alembic.upgrade()
        setup_default_permissions()
        print('reset done')

    manager.command(update_ldap)


if __name__ == "__main__":
    manager.run()
