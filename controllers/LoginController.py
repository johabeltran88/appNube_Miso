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
    Usuario, UsuarioSchema

usuario_schema = UsuarioSchema()

class VistaSignup(Resource):

    def post(self):
        usuario = Usuario.query.filter(Usuario.usuario == request.json["usuario"]).first()
        if usuario is None:
            if self.es_correo_valido(request.json["email"].lower()) == False:
                return {"mensaje": "El email no es válido"}, 422
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
    
    def es_correo_valido(self, correo):

        expresion_regular = r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"

        return re.match(expresion_regular, correo) is not None