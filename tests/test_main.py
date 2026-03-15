from typing import Any, List, Tuple
from unittest.mock import MagicMock

import pytest

import src.main as main_module


def _make_conn_with_counts(
    companies_count: int | None,
    vacancies_count: int | None,
) -> MagicMock:
    """
    Вспомогательная функция: создаёт мок-соединение с курсором,
    который возвращает заданные значения для двух последовательных fetchone().
    """
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cur

    # Настраиваем последовательность fetchone()
    fetch_results: List[Tuple[int] | None] = []
    fetch_results.append((companies_count,) if companies_count is not None else None)
    fetch_results.append((vacancies_count,) if vacancies_count is not None else None)

    cur.fetchone.side_effect = fetch_results
    return conn


def test_main_empty_tables_triggers_load_data_and_interface(monkeypatch: Any) -> None:
    """
    Если обе таблицы пустые (0, 0):
    - вызывается init_database()
    - вызывается load_data(conn)
    - создаётся DBManager
    - вызывается run_interface(db_manager)
    - всё завершается без исключений
    """
    # Мокаем init_database
    init_database_mock = MagicMock()
    monkeypatch.setattr(main_module, "init_database", init_database_mock)

    # Мокаем connect_to_db → возвращает соединение с (0, 0)
    conn = _make_conn_with_counts(0, 0)
    connect_to_db_mock = MagicMock(return_value=conn)
    monkeypatch.setattr(main_module, "connect_to_db", connect_to_db_mock)

    # Мокаем load_data
    load_data_mock = MagicMock()
    monkeypatch.setattr(main_module, "load_data", load_data_mock)

    # Мокаем DBManager
    db_manager_mock = MagicMock()
    db_manager_cls_mock = MagicMock(return_value=db_manager_mock)
    monkeypatch.setattr(main_module, "DBManager", db_manager_cls_mock)

    # Мокаем run_interface
    run_interface_mock = MagicMock()
    monkeypatch.setattr(main_module, "run_interface", run_interface_mock)

    # Мокаем logger, чтобы не писать в реальный лог
    logger_mock = MagicMock()
    monkeypatch.setattr(main_module, "logger", logger_mock)

    # Запускаем main()
    main_module.main()

    init_database_mock.assert_called_once()
    connect_to_db_mock.assert_called_once_with(main_module.settings.DB_NAME)
    load_data_mock.assert_called_once_with(conn)

    # Соединение, использованное в main, должно быть закрыто
    conn.close.assert_called_once()

    # DBManager создан и передан в интерфейс
    db_manager_cls_mock.assert_called_once()
    run_interface_mock.assert_called_once_with(db_manager_mock)
    db_manager_mock.close.assert_called_once()

    logger_mock.info.assert_any_call("Таблицы пустые — начинаем загрузку данных")
    logger_mock.info.assert_any_call("Программа завершена")


def test_main_existing_data_no_load_data(monkeypatch: Any) -> None:
    """
    Если обе таблицы непустые (>0, >0):
    - load_data НЕ вызывается
    - интерфейс запускается
    """
    init_database_mock = MagicMock()
    monkeypatch.setattr(main_module, "init_database", init_database_mock)

    conn = _make_conn_with_counts(5, 10)
    connect_to_db_mock = MagicMock(return_value=conn)
    monkeypatch.setattr(main_module, "connect_to_db", connect_to_db_mock)

    load_data_mock = MagicMock()
    monkeypatch.setattr(main_module, "load_data", load_data_mock)

    db_manager_mock = MagicMock()
    db_manager_cls_mock = MagicMock(return_value=db_manager_mock)
    monkeypatch.setattr(main_module, "DBManager", db_manager_cls_mock)

    run_interface_mock = MagicMock()
    monkeypatch.setattr(main_module, "run_interface", run_interface_mock)

    logger_mock = MagicMock()
    monkeypatch.setattr(main_module, "logger", logger_mock)

    main_module.main()

    load_data_mock.assert_not_called()
    logger_mock.info.assert_any_call("Данные уже присутствуют в таблицах")

    conn.close.assert_called_once()
    run_interface_mock.assert_called_once_with(db_manager_mock)
    db_manager_mock.close.assert_called_once()
    logger_mock.info.assert_any_call("Программа завершена")


@pytest.mark.parametrize(
    "companies_count, vacancies_count",
    [
        (0, 5),
        (5, 0),
    ],
)
def test_main_inconsistent_state_raises(
    monkeypatch: Any,
    companies_count: int,
    vacancies_count: int,
) -> None:
    """
    Если одна таблица пустая, а другая нет:
    - логируется ошибка
    - соединение закрывается
    - выбрасывается RuntimeError
    - интерфейс НЕ запускается
    """
    init_database_mock = MagicMock()
    monkeypatch.setattr(main_module, "init_database", init_database_mock)

    conn = _make_conn_with_counts(companies_count, vacancies_count)
    connect_to_db_mock = MagicMock(return_value=conn)
    monkeypatch.setattr(main_module, "connect_to_db", connect_to_db_mock)

    load_data_mock = MagicMock()
    monkeypatch.setattr(main_module, "load_data", load_data_mock)

    db_manager_cls_mock = MagicMock()
    monkeypatch.setattr(main_module, "DBManager", db_manager_cls_mock)

    run_interface_mock = MagicMock()
    monkeypatch.setattr(main_module, "run_interface", run_interface_mock)

    logger_mock = MagicMock()
    monkeypatch.setattr(main_module, "logger", logger_mock)

    with pytest.raises(RuntimeError, match="Неконсистентные данные в таблицах"):
        main_module.main()

    conn.close.assert_called_once()
    load_data_mock.assert_not_called()
    db_manager_cls_mock.assert_not_called()
    run_interface_mock.assert_not_called()

    logger_mock.error.assert_called_once_with(
        "Неконсистентное состояние БД: companies=%s, vacancies=%s",
        companies_count,
        vacancies_count,
    )
