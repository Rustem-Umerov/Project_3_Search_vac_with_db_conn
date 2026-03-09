from typing import Optional

import psycopg2
from psycopg2.extensions import connection, cursor
from psycopg2.sql import SQL, Identifier

from src.api_client import get_company, get_company_vacancies
from src.config import settings
from src.logger_setup import get_logger
from src.types_db_params import DbParams

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
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    vacancies_url TEXT,
                    alternate_url TEXT,
                    open_vacancies INTEGER,
                    description TEXT
                )
            """
            )

            logger.info("Создаём таблицу vacancies")

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS vacancies(
                    id TEXT PRIMARY KEY,
                    company_id TEXT REFERENCES companies(id),
                    title TEXT,
                    salary_from INTEGER,
                    salary_to INTEGER,
                    url TEXT,
                    alternate_url TEXT
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


def insert_company(conn: connection, company: dict) -> None:
    """
    Заполняет таблицу 'companies' данными о, переданной в функцию, компании.

    :param conn: Активное соединение с базой данных.
    :param company: Дынные о компании
    :raises Exception: Любая ошибка при заполнении таблицы.
    """

    try:
        company_id = company["id"]
        name = company["name"]
        vacancies_url = company["vacancies_url"]
        alternate_url = company["alternate_url"]
        open_vacancies = company["open_vacancies"]
        description = company.get("description")

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO companies (id, name, vacancies_url, alternate_url, open_vacancies, description)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    vacancies_url = EXCLUDED.vacancies_url,
                    alternate_url = EXCLUDED.alternate_url,
                    open_vacancies = EXCLUDED.open_vacancies,
                    description = EXCLUDED.description
                """,
                (company_id, name, vacancies_url, alternate_url, open_vacancies, description),
            )

        conn.commit()

    except Exception as e:
        logger.exception("Ошибка при заполнении таблицы (companies) данными: %s", e)
        raise


def insert_vacancies(conn: connection, vacancies: list[dict]) -> None:
    """
    Заполняет таблицу 'vacancies' данными о, переданном в функцию, списке компаний.

    :param conn: Активное соединение с базой данных.
    :param vacancies: Список с дынными о компаниях
    :raises Exception: Любая ошибка при заполнении таблицы.
    """

    try:
        with conn.cursor() as cur:

            for vac in vacancies:
                vacancy_id = vac["id"]
                company_id = vac["employer"]["id"]
                title = vac["name"]

                salary = vac.get("salary")  # получаю, для поиска salary_from и salary_to
                salary_from = salary.get("from") if salary else None
                salary_to = salary.get("to") if salary else None

                url = vac["url"]
                alternate_url = vac["alternate_url"]

                cur.execute(
                    """
                    INSERT INTO vacancies (id, company_id, title, salary_from, salary_to, url, alternate_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        salary_from = EXCLUDED.salary_from,
                        salary_to = EXCLUDED.salary_to,
                        url = EXCLUDED.url,
                        alternate_url = EXCLUDED.alternate_url
                    """,
                    (vacancy_id, company_id, title, salary_from, salary_to, url, alternate_url),
                )

        conn.commit()

    except Exception as e:
        logger.exception("Ошибка при заполнении таблицы (vacancies) данными: %s", e)
        raise


def load_data(conn: connection) -> None:
    """
    Функция получает данные о компании, список вакансии от компании и записывает все данные в таблицу.

    :param conn: Активное соединение с базой данных.
    """

    for company_id in EMPLOYERS_ID:
        logger.info("Начинаем загрузку данных для компании %s", company_id)

        # Получаю данные о компании
        company_data = get_company(company_id)

        # Записываю данные компании в таблицу
        insert_company(conn, company_data)

        # Получаю список вакансии
        company_vacancies = get_company_vacancies(company_id)
        logger.info("Получено %s вакансий для компании %s", len(company_vacancies), company_id)

        # Записываю вакансии в таблицу
        insert_vacancies(conn, company_vacancies)

        logger.info("Загрузка данных для компании %s завершена", company_id)
