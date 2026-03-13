from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def temp_logs_dir(tmp_path: Path) -> Path:
    """
    Временная директория для логов.
    Используется при тестировании get_logger с log_file.
    """

    return tmp_path


@pytest.fixture
def mock_session_get() -> Generator[MagicMock, None, None]:
    """
    Фикстура для мокирования session.get.
    Возвращает мок-объект, который перехватывает HTTP-запросы.
    """
    with patch("src.api_client.session.get") as mock_get:
        yield mock_get


@pytest.fixture
def mock_response() -> MagicMock:
    """
    Создаёт мок-объект ответа requests.Response.
    У него есть методы raise_for_status() и json().
    """
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    return resp


@pytest.fixture
def mock_connect() -> Generator[MagicMock, None, None]:
    """
    Мок psycopg2.connect, возвращающий мок‑соединение.
    """
    with patch("src.db_creator.psycopg2.connect") as mock_conn:
        conn = MagicMock()
        conn.cursor.return_value = MagicMock()
        mock_conn.return_value = conn
        yield mock_conn


@pytest.fixture
def mock_connection() -> MagicMock:
    """
    Мок‑соединение с БД.
    """
    conn = MagicMock()
    cursor = MagicMock()

    # cursor.__enter__ должен вернуть сам cursor
    cursor.__enter__.return_value = cursor
    cursor.__exit__.return_value = False

    conn.cursor.return_value = cursor
    return conn
