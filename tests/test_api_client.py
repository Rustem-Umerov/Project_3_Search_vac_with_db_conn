from unittest.mock import MagicMock

import pytest

from src.api_client import (
    api_request,
    get_company,
    get_company_vacancies,
    require_key,
    validate_company_response,
    validate_vacancies_response,
)

# api_request
# -----------------------------


def test_api_request_success(mock_session_get: MagicMock, mock_response: MagicMock) -> None:
    """Проверяет успешный возврат JSON-словаря при корректном ответе API."""
    mock_response.json.return_value = {"ok": True}
    mock_session_get.return_value = mock_response

    result = api_request(endpoint="/test", params={"a": 1})

    assert result == {"ok": True}
    mock_session_get.assert_called_once()


def test_api_request_non_dict(mock_session_get: MagicMock, mock_response: MagicMock) -> None:
    """Проверяет, что RuntimeError выбрасывается, если API вернул не dict."""
    mock_response.json.return_value = ["not", "a", "dict"]
    mock_session_get.return_value = mock_response

    with pytest.raises(RuntimeError):
        api_request(endpoint="/test")


def test_api_request_http_error(mock_session_get: MagicMock, mock_response: MagicMock) -> None:
    """Проверяет, что HTTP-ошибка пробрасывается наружу."""
    mock_response.raise_for_status.side_effect = Exception("HTTP error")
    mock_session_get.return_value = mock_response

    with pytest.raises(Exception):
        api_request(endpoint="/test")


# require_key
# -----------------------------


def test_require_key_success() -> None:
    """Проверяет, что require_key возвращает значение при наличии ключа."""
    d = {"a": 10}
    assert require_key(d, "a") == 10


def test_require_key_missing() -> None:
    """Проверяет, что require_key выбрасывает KeyError при отсутствии ключа."""
    with pytest.raises(KeyError):
        require_key({}, "missing")


# validate_company_response
# -----------------------------


def test_validate_company_response_success() -> None:
    """Проверяет успешную валидацию корректного ответа компании."""
    data = {
        "id": "123",
        "name": "Test Company",
        "vacancies_url": "http://example.com",
        "alternate_url": "http://example.com",
        "open_vacancies": 5,
        "description": "Some text",
    }

    validate_company_response(data)


@pytest.mark.parametrize("bad_field", ["id", "name", "vacancies_url", "alternate_url", "description"])
def test_validate_company_response_wrong_type_string_fields(bad_field: str) -> None:
    """Проверяет, что строковые поля должны быть str."""
    data = {
        "id": "123",
        "name": "Test Company",
        "vacancies_url": "http://example.com",
        "alternate_url": "http://example.com",
        "open_vacancies": 5,
        "description": "Some text",
    }
    data[bad_field] = 123

    with pytest.raises(TypeError):
        validate_company_response(data)


def test_validate_company_response_wrong_open_vacancies_type() -> None:
    """Проверяет, что open_vacancies должен быть int."""
    data = {
        "id": "123",
        "name": "Test Company",
        "vacancies_url": "http://example.com",
        "alternate_url": "http://example.com",
        "open_vacancies": "not-int",
        "description": "Some text",
    }

    with pytest.raises(TypeError):
        validate_company_response(data)


def test_validate_company_response_api_errors() -> None:
    """Проверяет, что наличие errors вызывает ValueError."""
    data = {"errors": ["Something bad"]}

    with pytest.raises(ValueError):
        validate_company_response(data)


def test_validate_company_response_empty() -> None:
    """Проверяет, что пустой словарь вызывает ValueError."""
    with pytest.raises(ValueError):
        validate_company_response({})


# get_company
# -----------------------------


def test_get_company_success(mock_session_get: MagicMock, mock_response: MagicMock) -> None:
    """Проверяет успешный возврат данных компании."""
    mock_response.json.return_value = {
        "id": "123",
        "name": "Test",
        "vacancies_url": "url",
        "alternate_url": "url",
        "open_vacancies": 1,
        "description": "desc",
    }
    mock_session_get.return_value = mock_response

    result = get_company("123")
    assert result["id"] == "123"


# -----------------------------
# TESTS FOR validate_vacancies_response
# -----------------------------


def test_validate_vacancies_response_success() -> None:
    """Проверяет успешную валидацию корректного ответа вакансий."""
    data = {
        "items": [{"a": 1}],
        "pages": 2,
        "found": 10,
        "page": 0,
    }

    validate_vacancies_response(data)


def test_validate_vacancies_response_items_not_list() -> None:
    """Проверяет, что items должен быть списком."""
    data = {
        "items": "not-list",
        "pages": 2,
        "found": 10,
        "page": 0,
    }

    with pytest.raises(TypeError):
        validate_vacancies_response(data)


def test_validate_vacancies_response_items_not_dict() -> None:
    """Проверяет, что элементы items должны быть dict."""
    data = {
        "items": ["not-dict"],
        "pages": 2,
        "found": 10,
        "page": 0,
    }

    with pytest.raises(TypeError):
        validate_vacancies_response(data)


@pytest.mark.parametrize("field", ["pages", "found", "page"])
def test_validate_vacancies_response_wrong_int_fields(field: str) -> None:
    """Проверяет, что pages, found и page должны быть int."""
    data = {
        "items": [{}],
        "pages": 2,
        "found": 10,
        "page": 0,
    }
    data[field] = "not-int"

    with pytest.raises(TypeError):
        validate_vacancies_response(data)


def test_validate_vacancies_response_api_errors() -> None:
    """Проверяет, что наличие errors вызывает ValueError."""
    data = {
        "items": [],
        "pages": 1,
        "found": 0,
        "page": 0,
        "errors": ["bad"],
    }

    with pytest.raises(ValueError):
        validate_vacancies_response(data)


# get_company_vacancies
# -----------------------------


def test_get_company_vacancies_single_page(mock_session_get: MagicMock, mock_response: MagicMock) -> None:
    """Проверяет обработку одной страницы вакансий."""
    mock_response.json.return_value = {
        "items": [{"id": 1}],
        "pages": 1,
        "found": 1,
        "page": 0,
    }
    mock_session_get.return_value = mock_response

    result = get_company_vacancies("123")

    assert result == [{"id": 1}]
    assert len(result) == 1


def test_get_company_vacancies_multiple_pages(mock_session_get: MagicMock) -> None:
    """Проверяет обработку нескольких страниц вакансий с использованием side_effect."""
    resp_page_0 = MagicMock()
    resp_page_0.raise_for_status = MagicMock()
    resp_page_0.json.return_value = {
        "items": [{"id": "p0"}],
        "pages": 3,
        "found": 3,
        "page": 0,
    }

    resp_page_1 = MagicMock()
    resp_page_1.raise_for_status = MagicMock()
    resp_page_1.json.return_value = {
        "items": [{"id": "p1"}],
        "pages": 3,
        "found": 3,
        "page": 1,
    }

    resp_page_2 = MagicMock()
    resp_page_2.raise_for_status = MagicMock()
    resp_page_2.json.return_value = {
        "items": [{"id": "p2"}],
        "pages": 3,
        "found": 3,
        "page": 2,
    }

    mock_session_get.side_effect = [resp_page_0, resp_page_1, resp_page_2]

    result = get_company_vacancies("123")

    assert result == [{"id": "p0"}, {"id": "p1"}, {"id": "p2"}]
    assert len(result) == 3
