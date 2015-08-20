from sigil.api import app, db
from sigil.permissions import setup_default_permissions
from flask_script import Manager, Server, prompt_pass
from sigil.models import User


@app.before_first_request
def create_db():
    db.create_all()
    setup_default_permissions()


manager = Manager(app)
manager.add_command("runserver", Server(host=app.config['HOST'],
                                        port=app.config['PORT']))


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


if __name__ == "__main__":
    manager.run()
