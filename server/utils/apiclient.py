import requests
import logging

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def call_meta_api(url, payload, timeout=20):
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "User-Agent": "insomnia/8.6.0"
    }
    try:
        response = requests.post(
            url, json=payload, headers=headers, timeout=timeout)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(
                f"API call failed with status code {response.status_code}: {response.text}")
            return {'error': True, 'status_code': response.status_code, 'text': response.text}
    except requests.exceptions.RequestException as e:
        logging.exception("Error calling meta API")
        return {'error': True, 'text': str(e)}


def get_cards_info(card_names, language):
    url = "https://meta.zeabur.app/cards/filter"
    payload = {"names": card_names}
    if language:
        payload["language"] = language
    return call_meta_api(url, payload)
