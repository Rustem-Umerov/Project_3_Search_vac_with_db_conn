import builtins
from typing import Any
from unittest.mock import MagicMock

import src.user_interface as ui

# show_menu
# ---------------------------------------------------------


def test_show_menu(monkeypatch: Any) -> None:
    """show_menu вызывает validating_user_input и возвращает его результат."""
    validate_mock = MagicMock(return_value=3)
    monkeypatch.setattr(ui, "validating_user_input", validate_mock)

    # Подавляем print, чтобы не засорять вывод
    monkeypatch.setattr(builtins, "print", MagicMock())

    result = ui.show_menu()
    assert result == 3
    validate_mock.assert_called_once()


# validating_user_input
# ---------------------------------------------------------


def test_validating_user_input_valid(monkeypatch: Any) -> None:
    """Корректный ввод возвращается сразу."""
    monkeypatch.setattr(builtins, "input", MagicMock(return_value="2"))
    logger_mock = MagicMock()
    monkeypatch.setattr(ui, "logger", logger_mock)

    menu = {1: "a", 2: "b", 3: "c"}
    result = ui.validating_user_input(menu=menu)
    assert result == 2
    logger_mock.info.assert_called_once()


def test_validating_user_input_invalid_then_valid(monkeypatch: Any) -> None:
    """Неверный ввод → повтор, затем корректный."""
    monkeypatch.setattr(
        builtins,
        "input",
        MagicMock(side_effect=["x", "5", "2"]),
    )
    print_mock = MagicMock()
    monkeypatch.setattr(builtins, "print", print_mock)

    logger_mock = MagicMock()
    monkeypatch.setattr(ui, "logger", logger_mock)

    menu = {1: "a", 2: "b", 3: "c"}
    result = ui.validating_user_input(menu=menu)

    assert result == 2
    assert logger_mock.error.call_count == 2
    logger_mock.info.assert_called_once()


# run_interface
# ---------------------------------------------------------


def test_run_interface_exit(monkeypatch: Any) -> None:
    """Если show_menu возвращает 6 — интерфейс завершается."""
    monkeypatch.setattr(ui, "show_menu", MagicMock(return_value=6))

    logger_mock = MagicMock()
    monkeypatch.setattr(ui, "logger", logger_mock)

    print_mock = MagicMock()
    monkeypatch.setattr(builtins, "print", print_mock)

    db_manager = MagicMock()

    ui.run_interface(db_manager)

    logger_mock.info.assert_any_call("Выполняется пункт меню: выход из программы")
    print_mock.assert_any_call("Выход из программы...")


def test_run_interface_calls_handlers(monkeypatch: Any) -> None:
    """Проверяем, что пункты меню вызывают нужные обработчики."""
    monkeypatch.setattr(
        ui,
        "show_menu",
        MagicMock(side_effect=[1, 2, 3, 4, 5, 6]),
    )

    handle_companies = MagicMock()
    monkeypatch.setattr(ui, "handle_show_companies", handle_companies)

    paginate_mock = MagicMock()
    monkeypatch.setattr(ui, "paginate_vacancies", paginate_mock)

    handle_avg = MagicMock()
    monkeypatch.setattr(ui, "handle_show_avg_salary", handle_avg)

    keyword_mock = MagicMock()
    monkeypatch.setattr(ui, "keyword_query", keyword_mock)

    db_manager = MagicMock()
    db_manager.get_all_vacancies.return_value = [{"x": 1}]
    db_manager.get_vacancies_with_higher_salary.return_value = [{"y": 2}]

    logger_mock = MagicMock()
    monkeypatch.setattr(ui, "logger", logger_mock)

    ui.run_interface(db_manager)

    handle_companies.assert_called_once()
    handle_avg.assert_called_once()
    keyword_mock.assert_called_once()
    assert paginate_mock.call_count == 2


# keyword_query
# ---------------------------------------------------------


def test_keyword_query(monkeypatch: Any) -> None:
    """keyword_query запрашивает ввод до непустой строки."""
    monkeypatch.setattr(
        builtins,
        "input",
        MagicMock(side_effect=["", "   ", "python"]),
    )

    paginate_mock = MagicMock()
    monkeypatch.setattr(ui, "paginate_vacancies", paginate_mock)

    logger_mock = MagicMock()
    monkeypatch.setattr(ui, "logger", logger_mock)

    db_manager = MagicMock()
    db_manager.get_vacancies_with_keyword.return_value = [{"a": 1}]

    ui.keyword_query(db_manager)

    db_manager.get_vacancies_with_keyword.assert_called_once_with("python")
    paginate_mock.assert_called_once()


# _checking_list_data
# ---------------------------------------------------------


def test_checking_list_data_valid(monkeypatch: Any) -> None:
    logger_mock = MagicMock()
    monkeypatch.setattr(ui, "logger", logger_mock)

    result = ui._checking_list_data(
        data=[{"a": 1}],
        method_name="m",
        empty_message="msg",
    )
    assert result is True
    logger_mock.debug.assert_called_once()


def test_checking_list_data_not_list(monkeypatch: Any) -> None:
    logger_mock = MagicMock()
    monkeypatch.setattr(ui, "logger", logger_mock)
    print_mock = MagicMock()
    monkeypatch.setattr(builtins, "print", print_mock)

    result = ui._checking_list_data(
        data="oops",  # type: ignore[arg-type]
        method_name="m",
        empty_message="msg",
    )
    assert result is False
    logger_mock.error.assert_called_once()


def test_checking_list_data_not_dicts(monkeypatch: Any) -> None:
    logger_mock = MagicMock()
    monkeypatch.setattr(ui, "logger", logger_mock)
    print_mock = MagicMock()
    monkeypatch.setattr(builtins, "print", print_mock)

    result = ui._checking_list_data(
        data=[1, 2, 3],  # type: ignore[list-item]
        method_name="m",
        empty_message="msg",
    )
    assert result is False
    logger_mock.error.assert_called_once()


def test_checking_list_data_empty(monkeypatch: Any) -> None:
    logger_mock = MagicMock()
    monkeypatch.setattr(ui, "logger", logger_mock)
    print_mock = MagicMock()
    monkeypatch.setattr(builtins, "print", print_mock)

    result = ui._checking_list_data(
        data=[],
        method_name="m",
        empty_message="msg",
    )
    assert result is False
    logger_mock.warning.assert_called_once()


# handle_show_companies
# ---------------------------------------------------------


def test_handle_show_companies(monkeypatch: Any) -> None:
    logger_mock = MagicMock()
    monkeypatch.setattr(ui, "logger", logger_mock)

    print_mock = MagicMock()
    monkeypatch.setattr(builtins, "print", print_mock)

    check_mock = MagicMock(return_value=True)
    monkeypatch.setattr(ui, "_checking_list_data", check_mock)

    db_manager = MagicMock()
    db_manager.get_companies_and_vacancies_count.return_value = [{"name": "A", "vacancy_count": 5}]

    ui.handle_show_companies(db_manager)

    check_mock.assert_called_once()
    logger_mock.info.assert_any_call("Получено %s компаний", 1)
    print_mock.assert_called()


# paginate_vacancies
# ---------------------------------------------------------


def test_paginate_vacancies_empty(monkeypatch: Any) -> None:
    """Если список пустой — проверка проваливается, пагинация не запускается."""
    logger_mock = MagicMock()
    monkeypatch.setattr(ui, "logger", logger_mock)

    check_mock = MagicMock(return_value=False)
    monkeypatch.setattr(ui, "_checking_list_data", check_mock)

    # ВАЖНО: не присваиваем результат, чтобы mypy не ругался
    ui.paginate_vacancies(
        data=[],
        method_name="m",
        menu_title="t",
    )

    logger_mock.warning.assert_called_once()


def test_paginate_vacancies_one_page(monkeypatch: Any) -> None:
    """Пагинация с одной страницей — next_or_prev_page возвращает None → выход."""
    logger_mock = MagicMock()
    monkeypatch.setattr(ui, "logger", logger_mock)

    check_mock = MagicMock(return_value=True)
    monkeypatch.setattr(ui, "_checking_list_data", check_mock)

    show_mock = MagicMock()
    monkeypatch.setattr(ui, "handle_show_vacancies", show_mock)

    next_mock = MagicMock(return_value=None)
    monkeypatch.setattr(ui, "next_or_prev_page", next_mock)

    print_mock = MagicMock()
    monkeypatch.setattr(builtins, "print", print_mock)

    data = [{"a": 1}]
    ui.paginate_vacancies(data=data, method_name="m", menu_title="t")

    show_mock.assert_called_once()
    next_mock.assert_called_once()
    logger_mock.info.assert_any_call("Пользователь вышел из пагинации")


# next_or_prev_page
# ---------------------------------------------------------


def test_next_or_prev_page_next(monkeypatch: Any) -> None:
    """Переход на следующую страницу."""
    monkeypatch.setattr(
        builtins,
        "input",
        MagicMock(return_value="1"),
    )
    logger_mock = MagicMock()
    monkeypatch.setattr(ui, "logger", logger_mock)

    result = ui.next_or_prev_page(start=0, page_size=10, total=30)
    assert result == 10


def test_next_or_prev_page_prev(monkeypatch: Any) -> None:
    """Переход на предыдущую страницу."""
    monkeypatch.setattr(
        builtins,
        "input",
        MagicMock(return_value="2"),
    )
    logger_mock = MagicMock()
    monkeypatch.setattr(ui, "logger", logger_mock)

    result = ui.next_or_prev_page(start=20, page_size=10, total=30)
    assert result == 10


def test_next_or_prev_page_exit(monkeypatch: Any) -> None:
    """Выход из пагинации."""
    monkeypatch.setattr(
        builtins,
        "input",
        MagicMock(return_value="3"),
    )
    logger_mock = MagicMock()
    monkeypatch.setattr(ui, "logger", logger_mock)

    result = ui.next_or_prev_page(start=0, page_size=10, total=30)
    assert result is None


# handle_show_vacancies
# ---------------------------------------------------------


def test_handle_show_vacancies(monkeypatch: Any) -> None:
    print_mock = MagicMock()
    monkeypatch.setattr(builtins, "print", print_mock)

    data: list[dict[str, Any]] = [
        {"name": "A", "title": "Dev", "salary_from": 100, "salary_to": 200, "url": "u"},
        {"name": "B", "title": "QA", "salary_from": None, "salary_to": None, "url": "x"},
    ]

    ui.handle_show_vacancies(data)

    assert print_mock.call_count == 2
