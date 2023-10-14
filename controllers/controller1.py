from flask import Blueprint

bpController1 = Blueprint('bpController1', __name__)

@bpController1.route('/route-1', methods=['GET'])
def route1():
    return 'Controller 1'