from typing import Optional
from unittest.mock import patch

import pytest

from src.config import Settings

# _get_env
# -----------------------------


def test_get_env_success() -> None:
    """Проверяет, что _get_env возвращает значение переменной окружения."""
    with patch("os.getenv", return_value="value"):
        assert Settings._get_env("DB_NAME") == "value"


def test_get_env_missing() -> None:
    """Проверяет, что _get_env выбрасывает ValueError, если переменная отсутствует."""
    with patch("os.getenv", return_value=None):
        with pytest.raises(ValueError):
            Settings._get_env("DB_NAME")


def test_get_env_empty_string() -> None:
    """Проверяет, что _get_env выбрасывает ValueError, если переменная пустая."""
    with patch("os.getenv", return_value="   "):
        with pytest.raises(ValueError):
            Settings._get_env("DB_NAME")


# _get_port
# -----------------------------


def test_get_port_success() -> None:
    """Проверяет, что _get_port корректно преобразует строку в число."""
    with patch("os.getenv", return_value="5432"):
        assert Settings._get_port("DB_PORT") == 5432


def test_get_port_missing() -> None:
    """Проверяет, что _get_port выбрасывает ValueError, если переменная отсутствует."""
    with patch("os.getenv", return_value=None):
        with pytest.raises(ValueError):
            Settings._get_port("DB_PORT")


def test_get_port_not_digit() -> None:
    """Проверяет, что _get_port выбрасывает ValueError, если значение не число."""
    with patch("os.getenv", return_value="not-a-number"):
        with pytest.raises(ValueError):
            Settings._get_port("DB_PORT")


# Settings CLASS
# -----------------------------


def test_settings_success() -> None:
    """
    Проверяет, что Settings корректно читает все переменные окружения
    и создаёт объект без ошибок.
    """
    env_values = {
        "DB_NAME": "testdb",
        "DB_USER": "user",
        "DB_PASSWORD": "pass",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
    }

    with patch("os.getenv", side_effect=lambda key: env_values[key]):
        settings = Settings()

        assert settings.DB_NAME == "testdb"
        assert settings.DB_USER == "user"
        assert settings.DB_PASSWORD == "pass"
        assert settings.DB_HOST == "localhost"
        assert settings.DB_PORT == 5432


@pytest.mark.parametrize("missing_key", ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST"])
def test_settings_missing_env(missing_key: str) -> None:
    """
    Проверяет, что Settings выбрасывает ValueError,
    если отсутствует любая строковая переменная окружения.
    """
    env_values: dict[str, Optional[str]] = {
        "DB_NAME": "testdb",
        "DB_USER": "user",
        "DB_PASSWORD": "pass",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
    }
    env_values[missing_key] = None

    with patch("os.getenv", side_effect=lambda key: env_values[key]):
        with pytest.raises(ValueError):
            Settings()


def test_settings_invalid_port() -> None:
    """Проверяет, что Settings выбрасывает ValueError, если DB_PORT не число."""
    env_values = {
        "DB_NAME": "testdb",
        "DB_USER": "user",
        "DB_PASSWORD": "pass",
        "DB_HOST": "localhost",
        "DB_PORT": "not-int",
    }

    with patch("os.getenv", side_effect=lambda key: env_values[key]):
        with pytest.raises(ValueError):
            Settings()
