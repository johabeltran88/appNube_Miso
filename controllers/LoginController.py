from flask import request
from flask_jwt_extended import jwt_required, create_access_token
from flask_restful import Resource
from datetime import datetime
import hashlib
import string
from marshmallow import Schema, fields

from models import \
    db, \
    Usuario, UsuarioSchema

usuario_schema = UsuarioSchema()

class VistaSignup(Resource):

    def post(self):
        usuario = Usuario.query.filter(Usuario.usuario == request.json["usuario"]).first()
        if usuario is None:
            usuario = Usuario.query.filter(Usuario.email == request.json["email"]).first()
            if usuario is None:
                contrasena1 = request.json["password1"]
                contrasena2 = request.json["password2"]
                if(contrasena1 != contrasena2):
                    return {"mensaje": "El password1 no coincide con el password2"}, 422
                
                digits = string.digits
                special_chars = string.punctuation
                if(any(char in digits for char in contrasena1) and
                any(char in string.ascii_lowercase for char in contrasena1) and
                any(char in string.ascii_uppercase for char in contrasena1) and
                any(char in special_chars for char in contrasena1) and len(contrasena1) >= 8):
                    contrasena = hashlib.md5(request.json["password1"].encode('utf-8')).hexdigest()
                    nuevo_usuario = Usuario(usuario=request.json["usuario"], contrasena=contrasena, email=request.json["email"])
                    db.session.add(nuevo_usuario)
                    db.session.commit()
                    return {"mensaje": "usuario creado exitosamente", "id": nuevo_usuario.id}
                else:
                    return {"mensaje": "La contraseña debe tener al menos un caracter numérico, al menos una letra mayúscula y minúscula, al menos un caracter especial y debe tener mínimo 8 caracteres"}, 422

                
            else:
                return {"mensaje": "El email ya existe"}, 422
        else:
            return {"mensaje": "El usuario ya existe"}, 422