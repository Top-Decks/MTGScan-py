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
    print(f"Processing image type: {'base64' if is_base64_image(msg['image']) else 'URL'}")
    with app.app_context():
        deck, img = scan(scan_celery._rec, msg)
        img_url = scan_celery._oss.upload_img(img)
        sio = SocketIO(message_queue=REDIS_URL)
        # 避免在响应中包含原始base64数据
        origin_img = msg['image'] if not is_base64_image(msg['image']) else "[base64_image_data]"
        sio.emit("scan_result", {
                 "deck": deck.maindeck.cards, "result_img": img_url, "origin_img": origin_img}, room=msg["id"])


@celery.task(base=ScanTask)
def scan_text_only_celery(msg):
    print("scan_text_only_celery")
    print(f"Processing image type: {'base64' if is_base64_image(msg['image']) else 'URL'}")
    with app.app_context():
        deck, _ = scan(scan_text_only_celery._rec, msg)
        sio = SocketIO(message_queue=REDIS_URL)
        sio.emit("scan_text_result", {
                 "deck": deck.maindeck.cards, "sideboard": deck.sideboard.cards}, room=msg["id"])


def is_base64_image(image_data):
    """
    检测输入是否为base64编码的图片数据
    :param image_data: 输入的图片数据
    :return: True如果是base64，False如果是URL
    """
    if isinstance(image_data, str):
        # 检查是否是URL格式
        if image_data.startswith(('http://', 'https://')):
            return False
        # 检查是否是base64格式（通常很长且包含base64字符）
        if len(image_data) > 100 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in image_data):
            return True
    return False


def scan(rec, msg):
    """
    扫描图片并识别卡牌
    :param rec: MagicRecognition实例
    :param msg: 包含图片数据的消息
    :return: 识别结果和处理后的图片
    """
    azure = Azure()
    print("scan")
    
    image_input = msg["image"]
    
    # 检测输入类型并相应处理
    if is_base64_image(image_input):
        print("Processing base64 image")
        # 对于base64图片，需要传递给Azure OCR的特殊处理方法
        box_texts = azure.image_to_box_texts(image_input, False)  # False表示base64格式
    else:
        print("Processing URL image")
        # 对于URL图片，使用原有的处理方式
        box_texts = azure.image_to_box_texts(image_input, True)   # True表示URL格式
    
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
    """处理GET请求的图片扫描，通过URL参数传递图片URL"""
    rec = MagicRecognition(file_all_cards=str(DIR_DATA / "all_cards.txt"),
                           file_keywords=(DIR_DATA / "Keywords.json"),
                           max_ratio_diff=0.3)
    print("api_scan (GET)")
    print(f"Image data type: {'base64' if is_base64_image(url) else 'URL'}")
    deck, img = scan(rec, {"image": url})
    img_url = TXOSSUtil().upload_img(img)
    return jsonify({"maindeck": deck.maindeck.cards, "sideboard": deck.sideboard.cards, "result_img": img_url})


@app.route("/api/scan", methods=["POST"])
def api_scan_post():
    """处理POST请求的图片扫描，支持base64编码的图片数据"""
    rec = MagicRecognition(file_all_cards=str(DIR_DATA / "all_cards.txt"),
                           file_keywords=(DIR_DATA / "Keywords.json"),
                           max_ratio_diff=0.3)
    
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({"error": "Missing image data"}), 400
    
    print("api_scan (POST)")
    print(f"Image data type: {'base64' if is_base64_image(data['image']) else 'URL'}")
    
    deck, img = scan(rec, {"image": data['image']})
    img_url = TXOSSUtil().upload_img(img)
    return jsonify({"maindeck": deck.maindeck.cards, "sideboard": deck.sideboard.cards, "result_img": img_url})


@app.route("/api/text_only/<path:url>")
def api_scan_text_only(url):
    """处理GET请求的纯文本扫描，通过URL参数传递图片URL"""
    rec = MagicRecognition(file_all_cards=str(DIR_DATA / "all_cards.txt"),
                           file_keywords=(DIR_DATA / "Keywords.json"),
                           max_ratio_diff=0.3)
    print("api_scan_text_only (GET)")
    print(f"Image data type: {'base64' if is_base64_image(url) else 'URL'}")
    deck, _ = scan(rec, {"image": url})
    return jsonify({"maindeck": deck.maindeck.cards, "sideboard": deck.sideboard.cards})


@app.route("/api/text_only", methods=["POST"])
def api_scan_text_only_post():
    """处理POST请求的纯文本扫描，支持base64编码的图片数据"""
    rec = MagicRecognition(file_all_cards=str(DIR_DATA / "all_cards.txt"),
                           file_keywords=(DIR_DATA / "Keywords.json"),
                           max_ratio_diff=0.3)
    
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({"error": "Missing image data"}), 400
    
    print("api_scan_text_only (POST)")
    print(f"Image data type: {'base64' if is_base64_image(data['image']) else 'URL'}")
    
    deck, _ = scan(rec, {"image": data['image']})
    return jsonify({"maindeck": deck.maindeck.cards, "sideboard": deck.sideboard.cards})


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port="5002")
