import os

from flask import Flask
from models import db

database_uti = os.environ.get("DATABASE_URI")


class Commons:

    @staticmethod
    def init():
        app = Flask(__name__)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './miso-nube-credentials.json'
        app.config['SQLALCHEMY_DATABASE_URI'] = database_uti
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['JWT_SECRET_KEY'] = 'frase-secreta'
        app.config['PROPAGATE_EXCEPTIONS'] = True

        app_context = app.app_context()
        app_context.push()

        db.init_app(app)
        db.create_all()
        return app
