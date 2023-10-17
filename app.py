from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api

from controllers.controller1 import bpController1
from controllers.controller2 import bpController2
from controllers.LoginController import VistaSignup 
from controllers.LoginController import VistaLogIn

from models import db
from commons.commons import Commons
from controllers.task_controller import bluePrintTaskController

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dbapp.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'frase-secreta'
app.config['PROPAGATE_EXCEPTIONS'] = True

app_context = app.app_context()
app_context.push()

db.init_app(app)
db.create_all()

cors = CORS(app)

# Registrar los controladores en la aplicación
app.register_blueprint(bpController1)
app.register_blueprint(bpController2)

api = Api(app)
api.add_resource(VistaSignup, '/api/auth/signup')
api.add_resource(VistaLogIn, '/api/auth/login')

jwt = JWTManager(app)
app = Commons.init_db()
app.register_blueprint(bluePrintTaskController)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
