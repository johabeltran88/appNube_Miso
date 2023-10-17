from commons.commons import Commons
from controllers.task_controller import bluePrintTaskController

app = Commons.init_db()
app.register_blueprint(bluePrintTaskController)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
