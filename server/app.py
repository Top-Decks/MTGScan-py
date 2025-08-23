from utils.txoss import TXOSSUtil
import eventlet

# 在导入其他模块之前进行monkey patch
eventlet.monkey_patch()

from datetime import datetime
import base64
import os
from pathlib import Path
from celery import Celery, Task
from flask import Flask, jsonify, render_template, request
from mtgscan.ocr.azure import Azure
from mtgscan.text import MagicRecognition
from flask_socketio import SocketIO

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
        self._oss = TXOSSUtil()


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("scan")
def scan_io(msg):
    print("scan_io")
    scan_celery.delay(msg)


@socketio.on("scan_text_only")
def scan_text_only_io(msg):
    print("scan_text_only_io")
    scan_text_only_celery.delay(msg)


@celery.task(base=ScanTask)
def scan_celery(msg):
    print("scan_celery")
    with app.app_context():
        deck, img = scan(scan_celery._rec, msg)
        img_url = scan_celery._oss.upload_img(img)
        sio = SocketIO(message_queue=REDIS_URL)
        sio.emit("scan_result", {
                 "deck": deck.maindeck.cards, "result_img": img_url, "origin_img": msg['image']}, room=msg["id"])


@celery.task(base=ScanTask)
def scan_text_only_celery(msg):
    print("scan_text_only_celery")
    with app.app_context():
        deck, _ = scan(scan_text_only_celery._rec, msg)
        sio = SocketIO(message_queue=REDIS_URL)
        sio.emit("scan_text_result", {
                 "deck": deck.maindeck.cards, "sideboard": deck.sideboard.cards}, room=msg["id"])


def scan(rec, msg):
    azure = Azure()
    print("scan")
    box_texts = azure.image_to_box_texts(msg["image"], True)
    box_cards = rec.box_texts_to_cards(box_texts)
    rec._assign_stacked(box_texts, box_cards)
    deck = rec.box_texts_to_deck(box_texts)
    img = box_cards.get_image(msg.get("image_64", msg["image"]))
    return deck, img


@app.route("/api/fuzzy_search", methods=["POST"])
def api_search_cards():
    card_names_text = request.json["text"]  # 获取包含卡牌名称的字符串数组
    language = request.json.get("language", None)  # 获取语言
    rec = MagicRecognition(file_all_cards=str(DIR_DATA / "all_cards.txt"),
                           file_keywords=(DIR_DATA / "Keywords.json"),
                           max_ratio_diff=0.3)
    cards = []
    for text in card_names_text:
        card = rec._search(text)
        if card:
            cards.append(card)

    print("api_search_cards")
    print(cards)
    # box_cards = rec.box_texts_to_cards(box_texts)
    # deck = rec.box_texts_to_deck(box_texts)
    # cards_info = get_cards_info(cards, language)

    return jsonify({"cards_names": cards})


@app.route("/api/<path:url>")
def api_scan(url):
    rec = MagicRecognition(file_all_cards=str(DIR_DATA / "all_cards.txt"),
                           file_keywords=(DIR_DATA / "Keywords.json"),
                           max_ratio_diff=0.3)
    print("api_scan")
    print(url)
    deck, img = scan(rec, {"image": url})
    img_url = TXOSSUtil().upload_img(img)
    return jsonify({"maindeck": deck.maindeck.cards, "sideboard": deck.sideboard.cards, "result_img": img_url})


@app.route("/api/text_only/<path:url>")
def api_scan_text_only(url):
    rec = MagicRecognition(file_all_cards=str(DIR_DATA / "all_cards.txt"),
                           file_keywords=(DIR_DATA / "Keywords.json"),
                           max_ratio_diff=0.3)
    print("api_scan_text_only")
    print(url)
    deck, _ = scan(rec, {"image": url})
    return jsonify({"maindeck": deck.maindeck.cards, "sideboard": deck.sideboard.cards})


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port="5002")
