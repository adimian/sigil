from sigil.api import app, db
from sigil.permissions import setup_default_permissions
from flask_script import Manager


@app.before_first_request
def create_db():
    db.create_all()


manager = Manager(app)


@manager.command
def initdb():
    setup_default_permissions()


app.run(host=app.config['HOST'],
        port=app.config['PORT'])
