import hashlib
import re
import string


from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token

from models import \
    db, \
    Usuario, UsuarioSchema

bluePrintLoginController = Blueprint('bluePrintLoginController', __name__)
usuario_schema = UsuarioSchema()


@bluePrintLoginController.route("/api/auth/signup", methods=['POST'])
def signup():
    usuario = Usuario.query.filter(Usuario.usuario == request.json["usuario"]).first()
    if usuario is None:
        mensaje = es_correo_valido(request.json["email"].lower())
        if mensaje != "":
            return {"mensaje": mensaje}, 422
        else:
            contrasena1 = request.json["password1"]
            contrasena2 = request.json["password2"]

            mensaje = es_password_valido(contrasena1, contrasena2)
            if mensaje != "":
                return {"mensaje": mensaje}, 422
            else:
                contrasena = hashlib.md5(request.json["password1"].encode('utf-8')).hexdigest()
                nuevo_usuario = Usuario(usuario=request.json["usuario"], contrasena=contrasena,
                                        email=request.json["email"])
                db.session.add(nuevo_usuario)
                db.session.commit()
                return {"mensaje": "usuario creado exitosamente", "id": nuevo_usuario.id}
    else:
        return {"mensaje": "El usuario ya existe"}, 422


def es_password_valido(password1, password2):
    mensaje = ""
    if (password1 != password2):
        mensaje = "El password1 no coincide con el password2"
    else:
        digits = string.digits
        special_chars = string.punctuation

        if (not any(char in digits for char in password1) or
                not any(char in string.ascii_lowercase for char in password1) or
                not any(char in string.ascii_uppercase for char in password1) or
                not any(char in special_chars for char in password1) or len(password1) < 8):
            mensaje = "La contraseña debe tener al menos un caracter numérico, al menos una letra mayúscula y minúscula, al menos un caracter especial y debe tener mínimo 8 caracteres"

    return mensaje


def es_correo_valido(correo):
    mensaje = ""
    expresion_regular = r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"
    if re.match(expresion_regular, correo) == None:
        return "El email no es válido"

    usuario = Usuario.query.filter(Usuario.email == request.json["email"]).first()
    if usuario is not None:
        return "El email ya existe"

    return mensaje


@bluePrintLoginController.route("/api/auth/login", methods=['POST'])
def login():
    contrasena_encriptada = hashlib.md5(request.json["password"].encode('utf-8')).hexdigest()
    usuario = Usuario.query.filter(Usuario.usuario == request.json["username"],
                                   Usuario.contrasena == contrasena_encriptada).first()
    db.session.commit()
    if usuario is None:
        return {"mensaje": "Usuario o contraseña incorrectos"}, 404
    else:
        token_de_acceso = create_access_token(identity=usuario.id)
        return jsonify({"mensaje": "Inicio de sesión exitoso", "token": token_de_acceso, "id": usuario.id})
