from typing import Optional, TypedDict

import psycopg2
from psycopg2.extensions import connection, cursor
from psycopg2.sql import SQL, Identifier

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
    """
    Подключение к системной базе PostgreSQL (postgres) для административных операций.

    :raises Exception: Любая ошибка при создании базы данных.
    :return: (connection, cursor)
    """

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
        logger.exception("Ошибка подключения к PostgreSQL: %s", e)
        raise


def database_exists(*, cur: cursor, dbname: str) -> bool:
    """
    Проверяет, существует ли база данных с указанным именем.
    :param cur: Курсор psycopg2, используемый для выполнения SQL‑запросов.
    :param dbname: Название базы данных
    :raises Exception: Любая ошибка при создании базы данных.
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
        logger.exception("Ошибка при проверке существования базы %s: %s", dbname, e)
        raise


def create_database(dbname: str) -> None:
    """
    Создаёт новую базу данных PostgreSQL.

    :param dbname: Название базы данных, которую нужно создать.
    :raises Exception: Любая ошибка при создании базы данных.
    """

    conn: Optional[connection] = None
    cur: Optional[cursor] = None

    try:
        # Подключаемся к системной базе postgres
        conn, cur = connect_to_server()
        conn.autocommit = True

        logger.info("Создаём базу %s", dbname)
        cur.execute(SQL("CREATE DATABASE {}").format(Identifier(dbname)))
        logger.info("База %s успешно создана", dbname)

    except Exception as e:
        logger.exception("Ошибка при создании базы %s: %s", dbname, e)
        raise

    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


def connect_to_db(dbname: str) -> tuple[connection, cursor]:
    """
    Подключение к базе данных dbname.

    :param dbname: Название базы данных
    :raises Exception: Любая ошибка при подключении.
    :return: (connection, cursor)
    """

    try:
        params: DbParams = {
            "dbname": dbname,
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD,
            "host": settings.DB_HOST,
            "port": settings.DB_PORT,
        }

        logger.debug(
            "Параметры подключения: dbname=%s, user=%s, host=%s, port=%s",
            dbname,
            params["user"],
            params["host"],
            params["port"],
        )

        conn = psycopg2.connect(**params)
        cur = conn.cursor()

        logger.info("Успешное подключение к базе %s", dbname)
        return conn, cur

    except Exception as e:
        logger.exception("Ошибка подключения к базе %s: %s", dbname, e)
        raise


def create_tables(conn: connection) -> None:
    """
    Создаёт таблицы companies и vacancies в базе данных.

    :param conn: Активное соединение с базой данных.
    :raises Exception: Любая ошибка при создании таблиц.
    """

    try:
        with conn.cursor() as cur:
            logger.info("Создаём таблицу companies")

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS companies(
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    url TEXT,
                    description TEXT
                )
            """
            )

            logger.info("Создаём таблицу vacancies")

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS vacancies(
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER REFERENCES companies(id),
                    title TEXT,
                    salary_from INTEGER,
                    salary_to INTEGER,
                    url TEXT
                )
            """
            )

        conn.commit()
        logger.debug("Таблицы успешно созданы")

    except Exception as e:
        logger.exception("Ошибка при создании таблиц: %s", e)
        raise


def init_database(dbname: str = "hh_project") -> None:
    """
    Полная инициализация базы данных:
    - подключение к postgres
    - проверка существования базы
    - создание базы при необходимости
    - подключение к новой базе
    - создание таблиц
    """

    # 1. Подключаемся к postgres
    conn, cur = connect_to_server()

    # 2. Проверяем/создаём базу
    if not database_exists(cur=cur, dbname=dbname):
        create_database(dbname)

    # 3. Закрываем соединение к postgres
    cur.close()
    conn.close()

    # 4. Подключаемся к новой базе
    conn, cur = connect_to_db(dbname)

    # 5. Создаём таблицы
    create_tables(conn)

    # 6. Закрываем соединение к новой базе
    cur.close()
    conn.close()

    logger.info("Инициализация базы данных завершена")
