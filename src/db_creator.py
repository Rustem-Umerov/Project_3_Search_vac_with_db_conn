from typing import TypedDict

import psycopg2
from psycopg2.extensions import connection, cursor

from src.config import settings
from src.logger_setup import get_logger

logger = get_logger(__name__)


class DbParams(TypedDict):
    """Строго типизированный словарь с параметрами подключения к PostgreSQL."""

    dbname: str
    user: str
    password: str
    host: str
    port: int


def connect_to_server() -> tuple[connection, cursor]:
    """Подключение к системной базе PostgreSQL (postgres) для административных операций."""

    try:
        params: DbParams = {
            "dbname": "postgres",
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD,
            "host": settings.DB_HOST,
            "port": settings.DB_PORT,
        }

        logger.debug(
            "Параметры подключения: dbname=%s, user=%s, host=%s, port=%s",
            params["dbname"],
            params["user"],
            params["host"],
            params["port"],
        )

        conn = psycopg2.connect(**params)
        cur = conn.cursor()

        logger.info("Успешное подключение к PostgreSQL (postgres)")
        return conn, cur

    except Exception as e:
        logger.error("Ошибка подключения к PostgreSQL: %s", e)
        raise


def database_exists(*, cur: cursor, dbname: str) -> bool:
    """
    Проверяет, существует ли база данных с указанным именем.
    :param cur: Курсор psycopg2, используемый для выполнения SQL‑запросов.
    :param dbname: Имя базы данных
    :return: True/False
    """

    try:
        logger.debug("Проверяем существование базы %s", dbname)
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        rows = cur.fetchone()

        if rows:
            logger.info("База %s существует", dbname)
            return True
        else:
            logger.info("База %s не найдена", dbname)
            return False

    except Exception as e:
        logger.error("Ошибка при проверке существования базы %s: %s", dbname, e)
        raise
