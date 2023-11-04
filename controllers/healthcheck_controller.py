from flask import Blueprint, request, jsonify, url_for, send_from_directory

bluePrintHealthcheckController = Blueprint('bluePrintHealthcheckController', __name__)

CONTROLLER_ROUTE = '/healthcheck'


@bluePrintHealthcheckController.route(CONTROLLER_ROUTE, methods=['GET'])
def healthcheck():
    return "Application up...", 200
