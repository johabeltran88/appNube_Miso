from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api

from commons.commons import Commons
from controllers.login_controller import bluePrintLoginController
from controllers.healthcheck_controller import bluePrintHealthcheckController
from controllers.task_controller import bluePrintTaskController

app = Commons.init()

cors = CORS(app)

app.register_blueprint(bluePrintTaskController)
app.register_blueprint(bluePrintLoginController)
app.register_blueprint(bluePrintHealthcheckController)

api = Api(app)

jwt = JWTManager(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
