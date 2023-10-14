from flask import Flask
from controllers.controller1 import bpController1
from controllers.controller2 import bpController2

app = Flask(__name__)

# Registrar los controladores en la aplicación
app.register_blueprint(bpController1)
app.register_blueprint(bpController2)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
