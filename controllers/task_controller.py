import os

from flask import Blueprint, request, jsonify, url_for, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity

from commons.utils import Utils
from commons.video_format_enum import VideoFormatEnum
from models import db, Usuario, Task, TaskSchema

task_schema = TaskSchema()

bluePrintTaskController = Blueprint('bluePrintTaskController', __name__)

CONTROLLER_ROUTE = '/api/tasks'


@bluePrintTaskController.route(CONTROLLER_ROUTE, methods=['POST'])
@jwt_required()
def create_task():
    errors = []
    None if validate_file('fileName', VideoFormatEnum) is None else errors.append(
        validate_file('fileName', VideoFormatEnum))
    None if validate_blank('newFormat') is None else errors.extend(validate_blank('newFormat'))
    None if validate_value('newFormat', VideoFormatEnum) is None else errors.append(
        validate_value('newFormat', VideoFormatEnum))
    print('HASTA ACA LLEGUE')
    if len(errors) > 0:
        return {"errors": errors}, 400
    print('HASTA ACA LLEGUE 2')
    id_usuario = get_jwt_identity()
    print('HASTA ACA LLEGUE 3')
    file = request.files['fileName']
    file_extension = Utils.get_file_extension(file.filename)
    None if (validate_extension_equals(file_extension, request.form.get('newFormat')) is None) else errors.append(
        validate_extension_equals(file_extension, request.form.get('newFormat')))
    if len(errors) > 0:
        return {"errors": errors}, 400
    task = Task(fileName=request.files['fileName'].filename, newFormat=request.form.get('newFormat').upper(),
                status='uploaded', user_id=id_usuario)
    db.session.add(task)
    db.session.commit()
    file = request.files['fileName']
    file.save('./files/{}.{}'.format(task.id, file_extension))
    return task_schema.dump(task), 201


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

@bluePrintTaskController.route(CONTROLLER_ROUTE + '/<int:id>', methods=['GET'])
@jwt_required()
def get_task_by_id(id):
    id_usuario = get_jwt_identity()
    print(id_usuario)
    task = Task.query.filter(Task.id == id, Task.user_id == id_usuario).first()
    if task is None:
        return {"mensaje": "No existe una tarea con ese id asignado a su usuario"}, 422
    else:
        resultado = task_schema.dump(task)
        resultado['original_file'] = url_for('bluePrintTaskController.publish_file', file_name= str(task.id) + "." + task.fileName.split(".")[1])
        if(task.status == 'processed'):            
            resultado['converted_file'] = url_for('bluePrintTaskController.publish_file', file_name= str(task.id) + "_converted." + task.newFormat)
        else:
            resultado['converted_file'] = ''
        return jsonify(resultado)
    
@bluePrintTaskController.route(CONTROLLER_ROUTE + '/files/<file_name>')
def publish_file(file_name):
    basedir = os.path.realpath(os.path.dirname(os.getcwd()))
    data_dir = os.path.join(basedir, 'APPNUBE_MISO', 'files')
    print(data_dir)
    return send_from_directory(data_dir, file_name, as_attachment=True,cache_timeout=0)    


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
        try:
            # We get the original file location
            original_file_path = os.path.join("./files",
                                              "{}.{}".format(task.id, Utils.get_file_extension(task.fileName)))
            converted_file_path = os.path.join("./files", "{}_converted.{}".format(task.id, task.newFormat))

            # Attempt to remove the original file from local storage
            if os.path.exists(original_file_path):
                os.remove(original_file_path)

            # Attempt to remove the converted file from local storage
            if os.path.exists(converted_file_path):
                os.remove(converted_file_path)
        except Exception as e:
            # If there's an error deleting either file, return an error message
            return {"mensaje": "Error eliminando los archivos asociados a la tarea: {}".format(str(e))}, 500

        # If both files were deleted successfully, remove the task from the database
        db.session.delete(task)
        db.session.commit()
        return {"mensaje": "Tarea eliminada exitosamente"}, 200
    else:
        # If task status is not 'Disponible', return an error message
        return {"mensaje": "La tarea no se puede eliminar porque está en proceso de conversión"}, 422
