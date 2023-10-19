from flask import Blueprint, request
from flask_jwt_extended import jwt_required, create_access_token
from flask_restful import Resource
from datetime import datetime
import hashlib
import string
import re
from marshmallow import Schema, fields


from commons.utils import Utils
from commons.video_format_enum import VideoFormatEnum
from models import \
    db, \
    Usuario, UsuarioSchema, Task, TaskSchema

usuario_schema = UsuarioSchema()
task_schema = TaskSchema()

bluePrintTaskController = Blueprint('bluePrintTaskController', __name__)

CONTROLLER_ROUTE = '/api/tasks'


@bluePrintTaskController.route(CONTROLLER_ROUTE, methods=['POST'])
def create_task():
    errors = []
    None if validate_file('fileName', VideoFormatEnum) is None else errors.append(
        validate_file('fileName', VideoFormatEnum))
    None if validate_blank('newFormat') is None else errors.extend(validate_blank('newFormat'))
    None if validate_value('newFormat', VideoFormatEnum) is None else errors.append(
        validate_value('newFormat', VideoFormatEnum))
    if len(errors) > 0:
        return {"errors": errors}, 400
    file = request.files['fileName']
    file_extension = Utils.get_file_extension(file.filename)
    None if (validate_extension_equals(file_extension, request.form.get('newFormat')) is None) else errors.append(
        validate_extension_equals(file_extension, request.form.get('newFormat')))
    if len(errors) > 0:
        return {"errors": errors}, 400
    task = Task(fileName=request.files['fileName'].filename, newFormat=request.form.get('newFormat').upper(), status='uploaded')
    db.session.add(task)
    db.session.commit()
    file = request.files['fileName']
    file.save('./files/{}.{}'.format(task.id, file_extension))
    return taskSchema.dump(task), 201


def validate_blank(*fields):
    errors = []
    for field in fields:
        if not (request.form.get(field) and len(request.form.get(field)) > 0):
            errors.append("El campo {} es obligatorio y no debe estar vacío.".format(field))
    if len(errors) == 0:
        return None
    else:
        return errors


def validate_file(field, enum):
    if field not in request.files:
        return "No se encontró ningún archivo en la solicitud."
    file = request.files[field]
    if file.filename == '':
        return "No se seleccionó ningún archivo."
    if not Utils.get_file_extension(file.filename).upper() in enum.__members__:
        return "Solo se admiten archivos de extensión {}".format(", ".join(member for member in enum.__members__))
    return None


def validate_value(field, enum):
    if not request.form.get(field).upper() in enum.__members__:
        return "El campo {} solo admite los valores {}.".format(field, ", ".join(member for member in enum.__members__))
    return None


def validate_extension_equals(file_extension, new_format):
    if file_extension == new_format:
        return "El archivo seleccionado tiene el nuevo formato ingresado, no es necesario hacer la conversión."
    return None



@bluePrintTaskController.route(CONTROLLER_ROUTE + '/<int:id_usuario>', methods=['GET'])
@jwt_required()
def get_tasks_for_user(id_usuario):
    try:
        usuario = Usuario.query.filter(Usuario.id == id_usuario).first()
        if not usuario:
            return {"mensaje": "El usuario no existe"}, 422
        tasks = Task.query.filter(Task.usuario == usuario).all()
        return task_schema.dump(tasks, many=True), 200
    except Exception as e:
        return {"Ha sucedido un error al intentar obtener las tareas del usuario": str(e)}, 500  # You can decide on a more specific error message if needed

@bluePrintTaskController.route(CONTROLLER_ROUTE + '/<int:id_usuario>', methods=['DELETE'])
@jwt_required()
def delete_tasks_for_user(id_usuario):
    

