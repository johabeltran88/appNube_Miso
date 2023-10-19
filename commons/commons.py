from flask import Flask
from models import db


class Commons:

    @staticmethod
    def init_db():
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../db/db.sqlite'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        app_context = app.app_context()
        app_context.push()

        db.init_app(app)
        db.create_all()
        return app
