from typing import Optional, TypeVar

import requests

from src.logger_setup import get_logger

T = TypeVar("T")

logger = get_logger(__name__)

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


def api_request(*, endpoint: str, params: Optional[dict] = None) -> dict:
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
    logger.info("base_url = (%s), endpoint = (%s), готовый url = (%s)", BASE_URL, endpoint, url)

    response = session.get(url=url, params=params, timeout=5)
    response.raise_for_status()
    logger.info("Запрос к АПИ успешно прошел")

    data = response.json()

    if not isinstance(data, dict):
        logger.error("Ошибка: ответ от АПИ должен быть: dict, а получен %s", type(data).__name__)
        raise RuntimeError("Ожидался JSON-объект (dict), но пришло что-то другое")

    return data


def get_company(company_id: str) -> dict:
    """
    Функция получает информацию о компании от API hh.ru
    Формирует правильный endpoint и переиспользует функцию api_request для запроса к АПИ

    :param company_id: ID компании
    :return: Распарсенный JSON-ответ API.
    """

    logger.info("Полученное company_id = %s", company_id)
    endpoint = f"/employers/{company_id}"
    logger.info("Сформированный endpoint = %s", endpoint)

    company_data = api_request(endpoint=endpoint)  # запрос к апи
    validate_company_response(company_data)  # проверка ответа от апи
    return company_data


def validate_company_response(data: dict) -> None:
    """
    Валидирует структуру ответа эндпоинта /employers/{company_id}.

    :param data: Словарь с ответом от АПИ
    """

    # Проверка на пустой словарь
    if not data:
        logger.error("Словарь с ответом пустой")
        raise ValueError("Компания не найдена")

    # Проверяем ошибки API
    errors = data.get("errors")
    if errors:
        logger.error("API вернул ошибки: %s", errors)
        raise ValueError(f"API вернул ошибки: {errors}")

    # Проверяем наличие ключей
    company_id: str = require_key(data, "id")
    name: str = require_key(data, "name")
    vacancies_url: str = require_key(data, "vacancies_url")
    alternate_url: str = require_key(data, "alternate_url")
    open_vacancies: int = require_key(data, "open_vacancies")

    string_fields = {
        "id": company_id,
        "name": name,
        "vacancies_url": vacancies_url,
        "alternate_url": alternate_url,
    }
    # Проверка, что у значений правильный тип
    for key, value in string_fields.items():
        if not isinstance(value, str):
            logger.error("Поле '%s' должно быть str, получено: %s", key, type(value).__name__)
            raise TypeError(f"'{key}' должно быть str, получено: {type(value).__name__}")

    if not isinstance(open_vacancies, int):
        logger.error("Поле 'open_vacancies' должно быть int, получено: %s", type(open_vacancies).__name__)
        raise TypeError(f"'open_vacancies' должно быть int, получено: {type(open_vacancies).__name__}")


def get_company_vacancies(company_id: str) -> list[dict]:
    """
    Функция для получения вакансии определенной компании от API hh.ru
    Делает первый запрос к АПИ для получения данных.
    Далее циклом проходит по всем страницам от API hh.ru

    :param company_id: ID компании
    :return: Список вакансии
    """

    # Список для сбора вакансии
    total_vacancies: list[dict] = []

    logger.info("Полученное company_id = %s", company_id)
    endpoint = "/vacancies"
    logger.info("Сформированный endpoint = %s", endpoint)

    # Первый запрос
    logger.info("Обрабатываю страницу 0")
    first_request = api_request(endpoint=endpoint, params={"employer_id": company_id, "page": 0, "per_page": 100})

    # Валидация ответа от первого запроса
    validate_vacancies_response(first_request)

    # Определяю количество страниц
    total_pages = first_request["pages"]
    logger.info("Всего страниц: %s", total_pages)

    # Получаю список вакансии по ключу "items" и добавляю в total_vacancies
    zero_page_vacancies = first_request["items"]
    logger.info("На странице 0 получено вакансий: %s", len(zero_page_vacancies))
    total_vacancies.extend(zero_page_vacancies)

    # Цикл по всем страницам
    for page in range(1, total_pages):
        logger.info("Обрабатываю страницу %s из %s", page, total_pages)
        page_data = api_request(endpoint=endpoint, params={"employer_id": company_id, "page": page, "per_page": 100})
        validate_vacancies_response(page_data)  # валидация ответа
        page_vacancies = page_data["items"]  # получение списка вакансии по ключу "items"
        logger.info("На странице %s получено вакансий: %s", page, len(page_vacancies))
        total_vacancies.extend(page_vacancies)  # добавляю в total_vacancies

    logger.info("Итого, получено вакансии: %s", len(total_vacancies))
    return total_vacancies


def require_key(d: dict[str, T], key: str) -> T:
    """
    Проверяет наличие ключа и возвращает его значение.

    :param d: Словарь для проверки
    :param key: Название ключа
    :return: Если ключа нет ошибка KeyError, если ключ есть, то его значение.
    """

    if key not in d:
        logger.error("В ответе отсутствует обязательный ключ: %s", key)
        raise KeyError(f"Отсутствует ключ: {key}")
    return d[key]


def validate_vacancies_response(data: dict) -> None:
    """
    Валидирует структуру ответа эндпоинта /vacancies.

    :param data: Словарь с ответом от АПИ
    """

    # Проверяем наличие ключей
    items: list[dict] = require_key(data, "items")
    pages: int = require_key(data, "pages")
    found: int = require_key(data, "found")
    page: int = require_key(data, "page")

    # Проверяем типы
    if not isinstance(items, list):
        logger.error("Поле 'items' должно быть list, получено: %s", type(items).__name__)
        raise TypeError(f"'items' должно быть list, получено: {type(items).__name__}")

    if not all(isinstance(item, dict) for item in items):
        logger.error("Каждый элемент 'items' должен быть dict")
        raise TypeError("Каждый элемент 'items' должен быть dict")

    integer_fields = {
        "pages": pages,
        "found": found,
        "page": page,
    }

    for key, value in integer_fields.items():
        if not isinstance(value, int):
            logger.error("Поле '%s' должно быть int, получено: %s", key, type(value).__name__)
            raise TypeError(f"'{key}' должно быть int, получено: {type(value).__name__}")

    # Проверяем ошибки API
    errors = data.get("errors")
    if errors:
        logger.error("API вернул ошибки: %s", errors)
        raise ValueError(f"API вернул ошибки: {errors}")

    # Дополнительные логические проверки (необязательные, но полезные)
    if pages < 1:
        logger.warning("Поле 'pages' меньше 1 — возможно, вакансий нет.")
    if page < 0 or page >= pages:
        logger.warning("Некорректный номер страницы: page=%s, pages=%s", page, pages)
