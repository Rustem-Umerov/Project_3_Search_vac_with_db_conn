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
