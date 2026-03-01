from typing import Optional

import requests

EMPLOYERS_ID = [
    "2477650",  # ОАО Красный Октябрь
    "1740",  # Яндекс
    "745654",  # Литрес
    "87021",  # RWB (Wildberries & Russ)
    "2180",  # Ozon
    "3529",  # СБЕР
    "1025275",  # Сеть магазинов цифровой и бытовой техники DNS
    "78638",  # Т-Банк
    "4181",  # Банк ВТБ (ПАО)
    "080",  # Альфа-Банк
]

BASE_URL = "https://api.hh.ru"

session = requests.Session()
session.headers.update({"User-Agent": "HHClient"})


def api_request(endpoint: str, params: Optional[dict] = None) -> dict:
    """
    Выполняет GET-запрос к API hh.ru через заранее сконфигурированную сессию.

    Args:
        endpoint: Путь относительно базового URL (например, "employers/1740").
        params: Словарь параметров запроса (page, per_page и т.д.).

    Returns:
        dict: Распарсенный JSON-ответ API.

    Raises:
        HTTPError: Если сервер вернул статус-код не 200.
        RuntimeError: Если API вернул не JSON-объект (dict).
    """

    url = BASE_URL + "/" + endpoint.lstrip("/")

    response = session.get(url=url, params=params, timeout=5)
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):
        raise RuntimeError("Ожидался JSON-объект (dict), но пришло что-то другое")

    return data
