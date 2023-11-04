import os

from celery import Celery
from celery.utils.log import get_task_logger
from google.cloud import storage
from moviepy.video.io.VideoFileClip import VideoFileClip

from commons.commons import Commons
from commons.utils import Utils
from controllers.task_controller import BUCKET_NAME
from models import Task, TaskSchema, db

rabbit_host = os.environ.get("RABBIT_HOST")

celery = Celery(
    'tasks',
    broker='pyamqp://guest@{}//'.format('localhost' if rabbit_host is None else rabbit_host),
    backend='db+sqlite:///db.sqlite',
)

logger = get_task_logger(__name__)

taskSchema = TaskSchema()

CODECS = {
    "MP4": {
        "codec": "libx264"
    },
    "WEBM": {
        "codec": "libvpx",
        "audio_codec": "libvorbis"
    },
    "AVI": {
        "codec": "rawvideo"
    },
    "MPEG": {
        "codec": "mpeg1video",
        "audio_codec": "mp3"
    },
    "WMV": {
        "codec": "wmv2"
    }
}


@celery.task(name="read_record_and_send_message_convert_task")
def read_record_and_send_message_convert_task():
    Commons.init()
    tasks = Task.query.filter(Task.status == 'uploaded').all()
    for task in tasks:
        convert_file.delay(taskSchema.dump(task))
        task.status = 'processing'
        db.session.add(task)
        db.session.commit()


@celery.task(name="convert_file")
def convert_file(task):
    Commons.init()
    task = Task.query.filter(Task.id == task['id']).first()
    input_file = "./files/{}.{}".format(task.id, Utils.get_file_extension(task.fileName))
    output_file = "./files/{}_converted.{}".format(task.id, task.newFormat)
    try:
        download_from_bucket(task.id, Utils.get_file_extension(task.fileName))
        video_file_clip = VideoFileClip(input_file)
        codec = CODECS["{}".format(task.newFormat).upper()]
        if 'audio_codec' in codec:
            video_file_clip.write_videofile(output_file, codec=codec['codec'], audio_codec=codec['audio_codec'])
        else:
            video_file_clip.write_videofile(output_file, codec=codec['codec'])
        task.converted_file = upload_to_bucket("{}_converted".format(task.id), task.newFormat)
        task.status = 'processed'
    except Exception as exception:
        logger.error('Error en la conversion del archivo.', exception)
        task.converted_file = 'error'
        task.status = 'error'
    delete_file(input_file)
    delete_file(output_file)
    db.session.add(task)
    db.session.commit()


celery.conf.beat_schedule = {
    'schedule_read_record_and_send_convert_message_task': {
        'task': 'read_record_and_send_message_convert_task',
        'schedule': 10.0
    },
}


def download_from_bucket(file_name, file_extension):
    client = storage.Client()
    bucket = client.get_bucket(BUCKET_NAME)
    blob = bucket.blob('{}.{}'.format(file_name, file_extension))
    blob.download_to_filename('./files/{}.{}'.format(file_name, file_extension))


def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def upload_to_bucket(file_name, file_extension):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob('{}.{}'.format(file_name, file_extension))
    blob.upload_from_filename('./files/{}.{}'.format(file_name, file_extension))
    return blob.public_url
