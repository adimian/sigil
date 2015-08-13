from sigil.api import app, db


@app.before_first_request
def create_db():
    db.create_all()

app.run(host=app.config['HOST'],
        port=app.config['PORT'])
