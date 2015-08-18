from sigil.api import app, db
from sigil.permissions import setup_default_permissions
from flask_script import Manager, Server


@app.before_first_request
def create_db():
    db.create_all()
    setup_default_permissions()


manager = Manager(app)
manager.add_command("runserver", Server(host=app.config['HOST'],
                                        port=app.config['PORT']))

if __name__ == "__main__":
    manager.run()
