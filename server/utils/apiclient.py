import requests
import ssl


def call_meta_api(url, payload):
    try:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "User-Agent": "insomnia/8.6.0"
        }

        ssl._create_default_https_context = ssl._create_unverified_context

        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.verify_mode = ssl.CERT_REQUIRED

        response = requests.post(
            url, json=payload, headers=headers, ssl_context=context)
        if response.status_code == 200:
            return response.json()
        else:
            # print(response.text)
            # 处理错误情况
            return {'text': response.text}
    except requests.exceptions.RequestException as e:
        return {'text': f"调用 meta api 时出错：{str(e)}"}


def get_cards_info(card_names, language):
    url = "http://meta.zeabur.app/cards/filter"
    payload = {"names": card_names}
    if language == "Chinese Simplified":
        payload = {"names": card_names, "language": "Chinese Simplified"}
    ret = call_meta_api(url, payload)
    return ret
