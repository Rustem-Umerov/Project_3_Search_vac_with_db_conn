from typing import Optional

import psycopg2
from psycopg2.extensions import connection, cursor
from psycopg2.extras import DictCursor

from src.config import settings
from src.logger_setup import get_logger
from src.types_db_params import DbParams

logger = get_logger(__name__)


class DBManager:
    """Класс для управления подключением к PostgreSQL и выполнения SQL-запросов."""

    def __init__(self) -> None:
        """Устанавливает соединение с БД и создаёт курсор."""

        self.conn: connection = self.connect_to_db()
        if self.conn is None:
            raise RuntimeError("Не удалось установить соединение с базой данных.")

        self.cur: cursor = self.conn.cursor(cursor_factory=DictCursor)

    def connect_to_db(self) -> connection:
        """Подключается к PostgreSQL и возвращает объект соединения."""

        try:
            params: DbParams = {
                "dbname": settings.DB_NAME,
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

            conn: connection = psycopg2.connect(**params)
            conn.autocommit = True

            logger.info("Успешное подключение к PostgreSQL (%s)", params["dbname"])
            return conn

        except Exception as e:
            logger.error("Ошибка подключения к PostgreSQL (%s): %s", settings.DB_NAME, e)
            raise

    def close(self) -> None:
        """Закрывает курсор и соединение с базой данных."""

        if self.cur is not None and not self.cur.closed:
            self.cur.close()
            logger.debug("Курсор PostgreSQL закрыт.")

        if self.conn is not None and not self.conn.closed:
            self.conn.close()
            logger.debug("Соединение с PostgreSQL закрыто.")

    def get_companies_and_vacancies_count(self) -> list[dict]:
        """
        Делает SQL запрос для таблиц companies и vacancies
        и возвращает список словарей, на примере: {"name": "Azon", "vacancy_count": 10}.
        """

        self.cur.execute(
            """
            SELECT
                companies.name,
                COUNT(vacancies.id) AS vacancy_count
            FROM companies
            LEFT JOIN vacancies
                ON companies.id=vacancies.company_id
            GROUP BY companies.id, companies.name;
            """
        )

        result = self.cur.fetchall()
        return [dict(dict_row) for dict_row in result]

    def get_all_vacancies(self) -> list[dict]:
        """
        Возвращает список словарей, где каждая запись содержит название компании,
        название вакансии, диапазон зарплаты и ссылку на вакансию.
        """

        self.cur.execute(
            """
            SELECT
                companies.name,
                vacancies.title,
                vacancies.salary_from,
                vacancies.salary_to,
                vacancies.url
            FROM vacancies
            JOIN companies
                ON companies.id=vacancies.company_id
            """
        )

        result = self.cur.fetchall()
        return [dict(dict_row) for dict_row in result]

    def get_avg_salary(self) -> Optional[float]:
        """
        Получает среднею зарплату по всем вакансиям.
        Для каждой вакансии использует:
            (salary_from + salary_to) / 2, если оба значения заданы,
            salary_from, если задано только оно,
            salary_to, если задано только оно.
            Вакансии без указанных зарплат пропускаются.
        Если в конце нет не одной зарплаты, то возвращает None.
        Возвращает одно число — среднюю зарплату по всем подходящим вакансиям.
        """

        self.cur.execute(
            """
            SELECT salary_from, salary_to
            FROM vacancies
            """
        )
        rows = [dict(dict_row) for dict_row in self.cur.fetchall()]
        salary_list = []

        for d in rows:
            salary_from = d.get("salary_from")
            salary_to = d.get("salary_to")

            if isinstance(salary_from, int) and isinstance(salary_to, int):
                res = (salary_from + salary_to) / 2
                salary_list.append(res)

            elif isinstance(salary_from, int):
                salary_list.append(salary_from)

            elif isinstance(salary_to, int):
                salary_list.append(salary_to)

            else:
                continue

        if not salary_list:
            logger.warning(
                "Данные о заработной плате отсутствуют, поэтому расчет средней заработной платы не возможен."
            )
            return None

        avg_salary = sum(salary_list) / len(salary_list)
        logger.debug("Средняя заработная плата по всем вакансиям = %s", avg_salary)
        return avg_salary

    def get_vacancies_with_higher_salary(self) -> list[dict]:
        """
        Получает список всех вакансий, у которых зарплата выше средней по всем вакансиям.
        """

        avg_salary = self.get_avg_salary()
        if avg_salary is None:
            logger.warning(
                "Функция для расчета средней заработной платы (get_avg_salary) вернула 'None'. "
                "Произвести сравнение не с чем. Функция возвращает: []"
            )
            return []

        self.cur.execute(
            """
            SELECT *
            FROM vacancies
            JOIN companies
                ON companies.id=vacancies.company_id
            """
        )
        rows = [dict(dict_row) for dict_row in self.cur.fetchall()]
        result_data = []

        for salary_dict in rows:
            salary_from = salary_dict.get("salary_from")
            salary_to = salary_dict.get("salary_to")

            if isinstance(salary_from, int) and isinstance(salary_to, int):
                res = (salary_from + salary_to) / 2
                if res > avg_salary:
                    result_data.append(salary_dict)

            elif isinstance(salary_from, int):
                if salary_from > avg_salary:
                    result_data.append(salary_dict)

            elif isinstance(salary_to, int):
                if salary_to > avg_salary:
                    result_data.append(salary_dict)

            else:
                continue

        return result_data

    def get_vacancies_with_keyword(self, keyword: str) -> list[dict]:
        """
        Получает список всех вакансии, в название которых содержатся переданные в метод слова.
        :param keyword: Ключевое слово, для поиска вакансии.
        """

        self.cur.execute(
            """
            SELECT *
            FROM vacancies
            JOIN companies
                ON companies.id=vacancies.company_id
            WHERE title ILIKE %s
            """,
            (f"%{keyword}%",),
        )

        vacancy_list = [dict(dict_row) for dict_row in self.cur.fetchall()]
        return vacancy_list
