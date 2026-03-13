from unittest.mock import MagicMock, patch

import pytest

from src.db_creator import (
    EMPLOYERS_ID,
    connect_to_db,
    connect_to_server,
    create_database,
    create_tables,
    database_exists,
    init_database,
    insert_company,
    insert_vacancies,
    load_data,
)

# connect_to_server
# ---------------------------------------------------------


def test_connect_to_server_success(mock_connect: MagicMock) -> None:
    """Проверяет успешное подключение к postgres."""
    conn = connect_to_server()
    assert conn is mock_connect.return_value


def test_connect_to_server_error(mock_connect: MagicMock) -> None:
    """Проверяет, что ошибка подключения пробрасывается."""
    mock_connect.side_effect = Exception("connection error")

    with pytest.raises(Exception):
        connect_to_server()


# database_exists
# ---------------------------------------------------------


def test_database_exists_true(mock_connection: MagicMock) -> None:
    """Проверяет, что функция возвращает True, если база существует."""
    cur = mock_connection.cursor.return_value
    cur.fetchone.return_value = (1,)

    assert database_exists(cur=cur, dbname="testdb") is True


def test_database_exists_false(mock_connection: MagicMock) -> None:
    """Проверяет, что функция возвращает False, если база не существует."""
    cur = mock_connection.cursor.return_value
    cur.fetchone.return_value = None

    assert database_exists(cur=cur, dbname="testdb") is False


def test_database_exists_error(mock_connection: MagicMock) -> None:
    """Проверяет, что ошибка пробрасывается."""
    cur = mock_connection.cursor.return_value
    cur.execute.side_effect = Exception("sql error")

    with pytest.raises(Exception):
        database_exists(cur=cur, dbname="testdb")


# create_database
# ---------------------------------------------------------


def test_create_database_success(mock_connect: MagicMock) -> None:
    """Проверяет успешное создание базы."""
    conn = mock_connect.return_value
    cur = conn.cursor.return_value

    create_database("mydb")

    cur.execute.assert_called_once()
    conn.close.assert_called_once()


def test_create_database_error(mock_connect: MagicMock) -> None:
    """Проверяет, что ошибка пробрасывается."""
    conn = mock_connect.return_value
    conn.cursor.side_effect = Exception("cursor error")

    with pytest.raises(Exception):
        create_database("mydb")


# connect_to_db
# ---------------------------------------------------------


def test_connect_to_db_success(mock_connect: MagicMock) -> None:
    """Проверяет успешное подключение к базе."""
    conn = connect_to_db("mydb")
    assert conn is mock_connect.return_value


def test_connect_to_db_error(mock_connect: MagicMock) -> None:
    """Проверяет, что ошибка пробрасывается."""
    mock_connect.side_effect = Exception("db error")

    with pytest.raises(Exception):
        connect_to_db("mydb")


# create_tables
# ---------------------------------------------------------


def test_create_tables_success(mock_connection: MagicMock) -> None:
    """Проверяет успешное создание таблиц."""
    create_tables(mock_connection)

    cur = mock_connection.cursor.return_value
    assert cur.execute.call_count == 2
    mock_connection.commit.assert_called_once()


def test_create_tables_error(mock_connection: MagicMock) -> None:
    """Проверяет, что ошибка пробрасывается."""
    cur = mock_connection.cursor.return_value
    cur.execute.side_effect = Exception("sql error")

    with pytest.raises(Exception):
        create_tables(mock_connection)


# init_database
# ---------------------------------------------------------


def test_init_database_creates_db() -> None:
    """
    Проверяет, что init_database создаёт базу,
    если database_exists возвращает False.
    """
    with (
        patch("src.db_creator.connect_to_server") as mock_server,
        patch("src.db_creator.database_exists", return_value=False),
        patch("src.db_creator.create_database") as mock_create,
        patch("src.db_creator.connect_to_db") as mock_connect_db,
        patch("src.db_creator.create_tables"),
    ):

        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        mock_server.return_value = conn

        init_database("mydb")

        mock_create.assert_called_once_with("mydb")
        mock_connect_db.assert_called_once_with("mydb")


def test_init_database_no_creation() -> None:
    """
    Проверяет, что init_database НЕ создаёт базу,
    если database_exists возвращает True.
    """
    with (
        patch("src.db_creator.connect_to_server") as mock_server,
        patch("src.db_creator.database_exists", return_value=True),
        patch("src.db_creator.create_database") as mock_create,
        patch("src.db_creator.connect_to_db") as mock_connect_db,
        patch("src.db_creator.create_tables"),
    ):

        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        mock_server.return_value = conn

        init_database("mydb")

        mock_create.assert_not_called()
        mock_connect_db.assert_called_once_with("mydb")


# insert_company
# ---------------------------------------------------------


def test_insert_company_success(mock_connection: MagicMock) -> None:
    """Проверяет успешную вставку компании."""
    company = {
        "id": "1",
        "name": "Test",
        "vacancies_url": "url",
        "alternate_url": "alt",
        "open_vacancies": 10,
        "description": "desc",
    }

    insert_company(mock_connection, company)

    cur = mock_connection.cursor.return_value
    cur.execute.assert_called_once()
    mock_connection.commit.assert_called_once()


def test_insert_company_error(mock_connection: MagicMock) -> None:
    """Проверяет, что ошибка пробрасывается."""
    cur = mock_connection.cursor.return_value
    cur.execute.side_effect = Exception("sql error")

    with pytest.raises(Exception):
        insert_company(mock_connection, {"id": "1"})


# insert_vacancies
# ---------------------------------------------------------


def test_insert_vacancies_success(mock_connection: MagicMock) -> None:
    """Проверяет успешную вставку вакансий."""
    vacancies = [
        {
            "id": "v1",
            "employer": {"id": "1"},
            "name": "Dev",
            "salary": {"from": 100, "to": 200},
            "url": "url",
            "alternate_url": "alt",
        }
    ]

    insert_vacancies(mock_connection, vacancies)

    cur = mock_connection.cursor.return_value
    cur.execute.assert_called_once()
    mock_connection.commit.assert_called_once()


def test_insert_vacancies_error(mock_connection: MagicMock) -> None:
    """Проверяет, что ошибка пробрасывается."""
    cur = mock_connection.cursor.return_value
    cur.execute.side_effect = Exception("sql error")

    with pytest.raises(Exception):
        insert_vacancies(mock_connection, [{"id": "v1", "employer": {"id": "1"}}])


# load_data
# ---------------------------------------------------------


def test_load_data_success(mock_connection: MagicMock) -> None:
    """Проверяет, что load_data вызывает get_company, insert_company, get_company_vacancies, insert_vacancies."""
    with (
        patch("src.db_creator.get_company", return_value={"id": "1"}),
        patch("src.db_creator.insert_company") as mock_insert_company,
        patch("src.db_creator.get_company_vacancies", return_value=[{"id": "v1"}]),
        patch("src.db_creator.insert_vacancies") as mock_insert_vacancies,
    ):

        load_data(mock_connection)

        assert mock_insert_company.call_count == len(EMPLOYERS_ID)
        assert mock_insert_vacancies.call_count == len(EMPLOYERS_ID)
