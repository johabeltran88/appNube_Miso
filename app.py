from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api

from commons.commons import Commons
from controllers.LoginController import bluePrintLoginController
from controllers.task_controller import bluePrintTaskController


app = Commons.init()


cors = CORS(app)

# Registrar los controladores en la aplicación

app.register_blueprint(bluePrintTaskController)
app.register_blueprint(bluePrintLoginController)

api = Api(app)

jwt = JWTManager(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
