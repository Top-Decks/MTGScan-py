from flask_socketio import SocketIO
from mtgscan.text import MagicRecognition
from mtgscan.ocr.azure import Azure
from flask import Flask, jsonify, render_template
from celery import Celery, Task
from pathlib import Path
import os
import base64
import eventlet
from utils.oss import OSSUtil
from datetime import datetime
eventlet.monkey_patch()


DIR_DATA = Path(__file__).parent / "data"
REDIS_URL = os.environ.get('REDIS_URL')

app = Flask(__name__)
socketio = SocketIO(app, message_queue=REDIS_URL, cors_allowed_origins="*")
celery = Celery(app.name, broker=REDIS_URL, backend=REDIS_URL)
celery.conf.update(
    broker_connection_retry_on_startup=True
)


class ScanTask(Task):
    def __init__(self):
        self._rec = MagicRecognition(file_all_cards=str(DIR_DATA / "all_cards.txt"),
                                     file_keywords=(
                                         DIR_DATA / "Keywords.json"),
                                     max_ratio_diff=0.3)
        self._oss = OSSUtil()


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("scan")
def scan_io(msg):
    print("scan_io")
    scan_celery.delay(msg)


@celery.task(base=ScanTask)
def scan_celery(msg):
    print("scan_celery")
    deck, img = scan(scan_celery._rec, msg)
    img_url = scan_celery._oss.upload_img(img)
    sio = SocketIO(message_queue=REDIS_URL)
    sio.emit("scan_result", {
             "deck": deck.maindeck.cards, "image": img_url}, room=msg["id"])


def scan(rec, msg):
    azure = Azure()
    print("scan")
    box_texts = azure.image_to_box_texts(msg["image"], True)
    box_cards = rec.box_texts_to_cards(box_texts)
    rec._assign_stacked(box_texts, box_cards)
    deck = rec.box_texts_to_deck(box_texts)
    img = box_cards.get_image(msg.get("image_64", msg["image"]))
    return deck, img


@app.route("/api/<path:url>")
def api_scan(url):
    rec = MagicRecognition(file_all_cards=str(DIR_DATA / "all_cards.txt"),
                           file_keywords=(DIR_DATA / "Keywords.json"),
                           max_ratio_diff=0.3)
    print("api_scan")
    print(url)
    deck = scan(rec, url)
    return jsonify({"maindeck": deck.maindeck.cards, "sideboard": deck.sideboard.cards})


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port="5002")
