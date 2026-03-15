import os

from dotenv import load_dotenv

from src.logger_setup import get_logger

logger = get_logger(__name__)
load_dotenv()


class Settings:
    """Класс для загрузки данных из .env"""

    def __init__(self) -> None:
        """Инициализация и проверка всех переменных окружения из .env"""

        self.DB_NAME: str = self._get_env("DB_NAME")
        self.DB_USER: str = self._get_env("DB_USER")
        self.DB_PASSWORD: str = self._get_env("DB_PASSWORD")
        self.DB_HOST: str = self._get_env("DB_HOST")
        self.DB_PORT: int = self._get_port("DB_PORT")

    @staticmethod
    def _get_env(name: str) -> str:
        """
        Проверка, что переменная окружения задана

        :param name: Название переменной окружения
        :return: Значение переменной окружения
        """

        value = os.getenv(name)
        logger.debug("Чтение переменной окружения '%s': '%s'", name, value)
        if value is None or value.strip() == "":
            logger.warning("Переменная окружения '%s' не задана или пуста", name)
            raise ValueError(f"Ошибка конфигурации: переменная '{name}' не задана")
        return value

    @staticmethod
    def _get_port(name: str) -> int:
        """
        Проверка и преобразование порта в число

        :param name: Название переменной окружения
        :return: Значение переменной окружения
        """

        value = os.getenv(name)
        logger.debug("Чтение переменной окружения '%s': '%s'", name, value)
        if value is None or not value.isdigit():
            logger.warning("Переменная окружения '%s' должна быть числом, текущее значение: '%s'", name, value)
            raise ValueError(f"Ошибка конфигурации: переменная '{name}' должна быть числом")
        return int(value)


# Создаём глобальный объект настроек
settings = Settings()
