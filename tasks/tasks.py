from celery import Celery
from celery.utils.log import get_task_logger
from moviepy.video.io.VideoFileClip import VideoFileClip

from commons.utils import Utils
from models import Task, TaskSchema, db
from commons.commons import Commons

celery = Celery(
    'tasks',
    broker='pyamqp://guest@localhost//',
    backend='db+sqlite:///db.sqlite',
)

logger = get_task_logger(__name__)

taskSchema = TaskSchema()

CODECS = {
    "WEBM MP4": {
        "codec": "libx264"
    },
    "AVI MP4": {
        "codec": "libx264"
    },
    "MPEG MP4": {
        "codec": "libx264"
    },
    "WMV MP4": {
        "codec": "libx264"
    },
    "MP4 WEBM": {
        "codec": "libvpx",
        "audio_codec": "libvorbis"
    },
    "AVI WEBM": {
        "codec": "libvpx",
        "audio_codec": "libvorbis"
    },
    "MPEG WEBM": {
        "codec": "libvpx",
        "audio_codec": "libvorbis"
    },
    "WMV WEBM": {
        "codec": "libvpx",
        "audio_codec": "libvorbis"
    },
    "MP4 AVI": {
        "codec": "rawvideo"
    },
    "WEBM AVI": {
        "codec": "rawvideo"
    },
    "MPEG AVI": {
        "codec": "rawvideo"
    },
    "WMV AVI": {
        "codec": "rawvideo"
    },
    "MP4 MPEG": {
        "codec": "mpeg1video",
        "audio_codec": "mp3"
    },
    "WEBM MPEG": {
        "codec": "mpeg1video",
        "audio_codec": "mp3"
    },
    "AVI MPEG": {
        "codec": "mpeg1video",
        "audio_codec": "mp3"
    },
    "WMV MPEG": {
        "codec": "mpeg1video",
        "audio_codec": "mp3"
    },
    "MP4 WMV": {
        "codec": "wmv2"
    },
    "WEBM WMV": {
        "codec": "wmv2"
    },
    "AVI WMV": {
        "codec": "wmv2"
    },
    "MPEG WMV": {
        "codec": "wmv2"
    },
}


@celery.task(name="read_record_and_send_message_convert_task")
def read_record_and_send_message_convert_task():
    Commons.init_db()
    tasks = Task.query.filter(Task.status == 'uploaded').all()
    for task in tasks:
        convert_file.delay(taskSchema.dump(task))
        task.status = 'processing'
        db.session.add(task)
        db.session.commit()


@celery.task(name="convert_file")
def convert_file(task):
    Commons.init_db()
    task = Task.query.filter(Task.id == task['id']).first()
    input_file = "./files/{}.{}".format(task.id, Utils.get_file_extension(task.fileName))
    output_file = "./files/{}_converted.{}".format(task.id, task.newFormat)
    try:
        video_file_clip = VideoFileClip(input_file)
        codec = CODECS["{} {}".format(Utils.get_file_extension(input_file), task.newFormat).upper()]
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
