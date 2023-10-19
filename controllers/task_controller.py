from flask import Blueprint, request, jsonify, url_for, send_from_directory
from datetime import datetime
from commons.utils import Utils
from commons.video_format_enum import VideoFormatEnum
from models import db, Task, TaskSchema
import os

bluePrintTaskController = Blueprint('bluePrintTaskController', __name__)

CONTROLLER_ROUTE = '/api/tasks'

taskSchema = TaskSchema()


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


@bluePrintTaskController.route(CONTROLLER_ROUTE + '/<int:id>', methods=['GET'])
def get_task_by_id(id):
    task = Task.query.filter(Task.id == id).first()
    if task is None:
        return {"mensaje": "No existe una tarea con ese id"}, 422
    else:
        resultado = taskSchema.dump(task)
        resultado['original_file'] = url_for('bluePrintTaskController.publish_file', file_name= str(task.id) + "." + task.fileName.split(".")[1])
        if(task.status == 'processed'):            
            resultado['converted_file'] = url_for('bluePrintTaskController.publish_file', file_name= str(task.id) + "." + task.newFormat)
        else:
            resultado['converted_file'] = ''
        return jsonify(resultado)
    
@bluePrintTaskController.route(CONTROLLER_ROUTE + '/files/<file_name>')
def publish_file(file_name):
    basedir = os.path.realpath(os.path.dirname(os.getcwd()))
    data_dir = os.path.join(basedir, 'APPNUBE_MISO', 'files')
    print(data_dir)
    return send_from_directory(data_dir, file_name, as_attachment=True,cache_timeout=0)    