from datetime import datetime
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fileName = db.Column(db.String(128))
    newFormat = db.Column(db.String(10))
    status = db.Column(db.String(10))
    timeStamp = db.Column(db.DateTime, default=datetime.utcnow)


class TaskSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        load_instance = True
