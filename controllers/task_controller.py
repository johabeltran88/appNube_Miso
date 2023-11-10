from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from google.cloud import storage

from commons.utils import Utils
from commons.video_format_enum import VideoFormatEnum
from models import db, Task, TaskSchema

task_schema = TaskSchema()

bluePrintTaskController = Blueprint('bluePrintTaskController', __name__)

CONTROLLER_ROUTE = '/api/tasks'

BUCKET_NAME = "file-converter-bucket"


@bluePrintTaskController.route(CONTROLLER_ROUTE, methods=['POST'])
@jwt_required()
def create_task():
    errors = []
    None if validate_file('fileName', VideoFormatEnum) is None else errors.append(
        validate_file('fileName', VideoFormatEnum))
    None if validate_blank('newFormat') is None else errors.extend(validate_blank('newFormat'))
    None if validate_value('newFormat', VideoFormatEnum) is None else errors.append(
        validate_value('newFormat', VideoFormatEnum))
    if len(errors) > 0:
        return {"errors": errors}, 400
    id_usuario = get_jwt_identity()
    file = request.files['fileName']
    file_extension = Utils.get_file_extension(file.filename)
    None if (validate_extension_equals(file_extension, request.form.get('newFormat')) is None) else errors.append(
        validate_extension_equals(file_extension, request.form.get('newFormat')))
    if len(errors) > 0:
        return {"errors": errors}, 400
    task = Task(
        fileName=request.files['fileName'].filename,
        newFormat=request.form.get('newFormat').upper(),
        status='uploaded',
        user_id=id_usuario,
        converted_file='pending'
    )
    db.session.add(task)
    db.session.commit()
    task.original_file = upload_to_bucket(request.files['fileName'], task.id, file_extension)
    db.session.add(task)
    db.session.commit()
    return task_schema.dump(task), 201


@bluePrintTaskController.route(CONTROLLER_ROUTE + '/<int:id>', methods=['GET'])
@jwt_required()
def get_task_by_id(id):
    id_usuario = get_jwt_identity()
    task = Task.query.filter(Task.id == id, Task.user_id == id_usuario).first()
    if task is None:
        return {"mensaje": "No existe una tarea con ese id asignado a su usuario"}, 422
    else:
        return jsonify(task_schema.dump(task))


@bluePrintTaskController.route(CONTROLLER_ROUTE, methods=['GET'])
@jwt_required()
def get_tasks_for_user():
    id_usuario = get_jwt_identity()
    try:
        tasks = Task.query.filter(Task.user_id == id_usuario).all()
        return {"task": [task_schema.dump(task) for task in tasks]}, 200
    except Exception as e:
        return {"Ha sucedido un error al intentar obtener las tareas del usuario": str(e)}, 500


@bluePrintTaskController.route(CONTROLLER_ROUTE + '/<int:id_task>', methods=['DELETE'])
@jwt_required()
def delete_tasks_for_user(id_task):
    id_usuario = get_jwt_identity()
    try:
        # Retrieve the task by id_task and id_usuario
        task = Task.query.filter(Task.id == id_task, Task.user_id == id_usuario).first()
        if not task:
            return {"mensaje": "La tarea no existe o no pertenece al usuario"}, 404
    except Exception as e:
        return {"Ha sucedido un error al intentar obtener la tarea del usuario": str(e)}, 500

        # If task status is 'Disponible', delete the associated files
    if task.status != 'processing':
        delete_from_bucket(task.id, Utils.get_file_extension(task.fileName))
        delete_from_bucket("{}_converted".format(task.id), task.newFormat)
        db.session.delete(task)
        db.session.commit()
        return {"mensaje": "Tarea eliminada exitosamente"}, 200
    else:
        # If task status is not 'Disponible', return an error message
        return {"mensaje": "La tarea no se puede eliminar porque está en proceso de conversión"}, 422


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
    if request.form.get(field) is not None and not request.form.get(field).upper() in enum.__members__:
        return "El campo {} solo admite los valores {}.".format(field, ", ".join(member for member in enum.__members__))
    return None


def validate_extension_equals(file_extension, new_format):
    if file_extension == new_format:
        return "El archivo seleccionado tiene el nuevo formato ingresado, no es necesario hacer la conversión."
    return None


def upload_to_bucket(file, file_name, file_extension):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob('{}.{}'.format(file_name, file_extension))
    blob.upload_from_file(file, content_type=file.content_type)
    return blob.public_url


def delete_from_bucket(file_name, file_extension):
    client = storage.Client()
    bucket = client.get_bucket(BUCKET_NAME)
    blob = bucket.blob('{}.{}'.format(file_name, file_extension))
    if blob.exists():
        blob.delete()
