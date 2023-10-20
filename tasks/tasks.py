import os

from celery import Celery
from celery.utils.log import get_task_logger
from moviepy.video.io.VideoFileClip import VideoFileClip

from commons.utils import Utils
from models import Task, TaskSchema, db
from commons.commons import Commons

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
        video_file_clip = VideoFileClip(input_file)
        codec = CODECS["{}".format(task.newFormat).upper()]
        logger.info(codec)
        if 'audio_codec' in codec:
            video_file_clip.write_videofile(output_file, codec=codec['codec'], audio_codec=codec['audio_codec'])
        else:
            video_file_clip.write_videofile(output_file, codec=codec['codec'])
        task.status = 'processed'
    except Exception as exception:
        logger.error('Error en la conversion del archivo.', exception)
        task.status = 'error'
    db.session.add(task)
    db.session.commit()


celery.conf.beat_schedule = {
    'schedule_read_record_and_send_convert_message_task': {
        'task': 'read_record_and_send_message_convert_task',
        'schedule': 10.0
    },
}
