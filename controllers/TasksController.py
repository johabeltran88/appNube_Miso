from flask import request
from flask_jwt_extended import jwt_required, create_access_token
from flask_restful import Resource
from datetime import datetime
import hashlib
import string
import re
from marshmallow import Schema, fields

from models import \
    db, \
    Usuario, UsuarioSchema, Task, TaskSchema

usuario_schema = UsuarioSchema()
task_schema = TaskSchema()

class VistaTasks(Resource):
    @jwt_required()
    def get(self, id_usuario):
        # Add a try catch block, to identify if the user exists
        try:
            usuario = Usuario.query.filter(Usuario.id == id_usuario).first()
            tasks = Task.query.filter(Task.usuario == usuario).all()
            return task_schema.dump(tasks, many=True), 200
        except:
            return {"mensaje": "El usuario no existe"}, 422
    @jwt_required()
    def delete(slef, id_task):
        task = Task.query.filter(Task.id == id_task).first()
        if task is None:
            return {"mensaje": "La tarea no existe"}, 422
        else:
            db.session.delete(task)
            db.session.commit()
            return {"mensaje": "Tarea eliminada exitosamente"}, 200
        #Hace falta aniadir bloque para eliminar archivos asociados a la tarea.
            
        
