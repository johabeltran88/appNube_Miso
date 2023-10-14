from flask import Blueprint

bpController2 = Blueprint('bpController2', __name__)

@bpController2.route('/route-2', methods=['GET'])
def route1():
    return 'Controller 2'