import os

from flask import Flask
from models import db


class Commons:

    @staticmethod
    def init():
        app = Flask(__name__)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './miso-nube-932084c5cff6.json'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:})^M^JeM?H0+=e(-@35.233.184.37/file-converter'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['JWT_SECRET_KEY'] = 'frase-secreta'
        app.config['PROPAGATE_EXCEPTIONS'] = True

        app_context = app.app_context()
        app_context.push()

        db.init_app(app)
        db.create_all()
        return app
