from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from src.db_manager import DBManager

# __init__
# ---------------------------------------------------------


def test_dbmanager_init_success(mock_connect_db_manager: MagicMock) -> None:
    """Проверяет успешную инициализацию DBManager."""
    db = DBManager()
    assert db.conn is mock_connect_db_manager.return_value
    assert db.cur is mock_connect_db_manager.return_value.cursor.return_value


def test_dbmanager_init_fail() -> None:
    """Проверяет, что ошибка подключения пробрасывается."""
    with patch("src.db_manager.psycopg2.connect", side_effect=Exception("conn error")):
        with pytest.raises(Exception):
            DBManager()


# close()
# ---------------------------------------------------------


def test_close_success(db: DBManager) -> None:
    """Проверяет корректное закрытие курсора и соединения."""

    cur = db.cur  # type: ignore[assignment]
    conn = db.conn  # type: ignore[assignment]

    assert isinstance(cur, MagicMock)
    assert isinstance(conn, MagicMock)

    cur.closed = False
    conn.closed = False

    db.close()

    cur.close.assert_called_once()
    conn.close.assert_called_once()


def test_close_already_closed(db: DBManager) -> None:
    """Проверяет, что повторное закрытие не вызывает ошибок."""

    cur = db.cur  # type: ignore[assignment]
    conn = db.conn  # type: ignore[assignment]

    assert isinstance(cur, MagicMock)
    assert isinstance(conn, MagicMock)

    cur.closed = True
    conn.closed = True

    # Метод не должен упасть
    db.close()


# get_companies_and_vacancies_count
# ---------------------------------------------------------


def test_get_companies_and_vacancies_count(db: DBManager) -> None:
    """Проверяет корректное выполнение SQL и преобразование результата."""

    cur = db.cur  # type: ignore[assignment]
    assert isinstance(cur, MagicMock)

    cur.fetchall.return_value = [
        {"name": "Test", "vacancy_count": 5},
        {"name": "Ozon", "vacancy_count": 10},
    ]

    result = db.get_companies_and_vacancies_count()

    assert result == [
        {"name": "Test", "vacancy_count": 5},
        {"name": "Ozon", "vacancy_count": 10},
    ]

    cur.execute.assert_called_once()


# get_all_vacancies
# ---------------------------------------------------------


def test_get_all_vacancies(db: DBManager) -> None:
    """Проверяет получение списка всех вакансий."""

    cur = db.cur  # type: ignore[assignment]
    assert isinstance(cur, MagicMock)

    cur.fetchall.return_value = [
        {"name": "Test", "title": "Dev", "salary_from": 100, "salary_to": 200, "url": "url"},
    ]

    result = db.get_all_vacancies()

    assert result == [
        {"name": "Test", "title": "Dev", "salary_from": 100, "salary_to": 200, "url": "url"},
    ]

    cur.execute.assert_called_once()


# get_avg_salary
# ---------------------------------------------------------


@pytest.mark.parametrize(
    "rows, expected",
    [
        ([{"salary_from": 100, "salary_to": 200}], 150.0),
        ([{"salary_from": 100, "salary_to": None}], 100.0),
        ([{"salary_from": None, "salary_to": 300}], 300.0),
        ([{"salary_from": None, "salary_to": None}], None),
        ([], None),
    ],
)
def test_get_avg_salary(db: DBManager, rows: List[Dict[str, Any]], expected: float | None) -> None:
    """Проверяет корректный расчёт средней зарплаты."""

    cur = db.cur  # type: ignore[assignment]
    assert isinstance(cur, MagicMock)

    cur.fetchall.return_value = rows

    result = db.get_avg_salary()
    assert result == expected


# get_vacancies_with_higher_salary
# ---------------------------------------------------------


def test_get_vacancies_with_higher_salary(db: DBManager) -> None:
    """Проверяет фильтрацию вакансий по средней зарплате."""

    db.get_avg_salary = MagicMock(return_value=150)  # type: ignore[assignment]

    cur = db.cur  # type: ignore[assignment]
    assert isinstance(cur, MagicMock)

    cur.fetchall.return_value = [
        {"salary_from": 200, "salary_to": None},
        {"salary_from": 100, "salary_to": None},
        {"salary_from": None, "salary_to": 300},
    ]

    result = db.get_vacancies_with_higher_salary()

    assert result == [
        {"salary_from": 200, "salary_to": None},
        {"salary_from": None, "salary_to": 300},
    ]


def test_get_vacancies_with_higher_salary_no_avg(db: DBManager) -> None:
    """Проверяет, что при avg_salary=None возвращается пустой список."""

    db.get_avg_salary = MagicMock(return_value=None)  # type: ignore[assignment]

    result = db.get_vacancies_with_higher_salary()
    assert result == []


# get_vacancies_with_keyword
# ---------------------------------------------------------


def test_get_vacancies_with_keyword(db: DBManager) -> None:
    """Проверяет поиск вакансий по ключевому слову."""

    cur = db.cur  # type: ignore[assignment]
    assert isinstance(cur, MagicMock)

    cur.fetchall.return_value = [
        {"title": "Python Developer"},
        {"title": "Senior Python Engineer"},
    ]

    result = db.get_vacancies_with_keyword("python")

    assert len(result) == 2
    cur.execute.assert_called_once()
