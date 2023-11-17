import json
import os

from google.cloud import pubsub_v1
from google.cloud import storage
from moviepy.video.io.VideoFileClip import VideoFileClip
from commons.commons import Commons
from commons.utils import Utils
from controllers.healthcheck_controller import bluePrintHealthcheckController
from models import Task, db
from flask_restful import Api

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './miso-nube-credentials.json'

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

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(os.environ.get("GCP_PROJECT_ID"),
                                                 os.environ.get("GCP_SUBSCRIPTION_NAME"))
topic_path = subscriber.topic_path(os.environ.get("GCP_PROJECT_ID"), os.environ.get("GCP_TOPIC_NAME"))


def download_from_bucket(file_name, file_extension):
    client = storage.Client()
    bucket = client.get_bucket(os.environ.get("GCP_BUCKET_NAME"))
    blob = bucket.blob('{}.{}'.format(file_name, file_extension))
    blob.download_to_filename('./files/{}.{}'.format(file_name, file_extension))


def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def upload_to_bucket(file_name, file_extension):
    client = storage.Client()
    bucket = client.bucket(os.environ.get("GCP_BUCKET_NAME"))
    blob = bucket.blob('{}.{}'.format(file_name, file_extension))
    blob.upload_from_filename('./files/{}.{}'.format(file_name, file_extension))
    return blob.public_url


def callback(message):
    data = json.loads(message.data)
    message.ack()
    Commons.init()
    while True:
        task = Task.query.filter(Task.id == int(data['id'])).first()
        if task is not None:
            break
    if task.status != 'processing':
        task.status = 'processing'
        db.session.add(task)
        db.session.commit()
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
            task.converted_file = 'error'
            task.status = 'error'
        delete_file(input_file)
        delete_file(output_file)
        db.session.add(task)
        db.session.commit()


subscription = subscriber.subscribe(subscription_path, callback=callback)

app = Commons.init()

app.register_blueprint(bluePrintHealthcheckController)

api = Api(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    try:
        subscription.result()
    except KeyboardInterrupt:
        subscription.close()
