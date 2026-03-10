from typing import Optional

from src.db_manager import DBManager
from src.logger_setup import get_logger

logger = get_logger(__name__)


def show_menu() -> int:
    """
    Выводит меню в консоль.
    Просит пользователя выбрать один из пунктов меню.
    Если пользователь делает не правильный ввод, то цикл повторяется.
    Функция возвращает номер пункта меню, который выбрал пользователь.
    """

    logger.debug("Вывод меню в консоль.")
    menu = {
        1: "Показать компании и количество вакансий",
        2: "Показать все вакансии",
        3: "Показать среднюю зарплату",
        4: "Показать вакансии с зарплатой выше средней",
        5: "Поиск вакансий по ключевому слову",
        6: "Выход",
    }

    print()
    print("=" * 44)
    print(f"{"_" * 20}МЕНЮ{"_" * 20}")
    print("-" * 44)
    print("Выберите пункт из меню и введете цифру")
    print("=" * 44)

    for key, value in menu.items():
        print(f"{key}: {value}")
    print("=" * 44)

    choice = validating_user_input(menu=menu)
    return choice


def validating_user_input(*, menu: dict[int, str], prompt: Optional[str] = None) -> int:
    """
    Функция-валидатор, для проверки пользовательского ввода.

    :param menu: Словарь меню
    :param prompt: Сообщение пользователю
    :return: Номер пункта, выбранного пользователем
    """

    if prompt is None:
        prompt = f"Введите цифру (от {min(menu)} до {max(menu)}) -----> "

    while True:
        user_input = input(prompt)

        if not user_input.isdigit() or int(user_input) not in menu:
            logger.error(
                "Пользователь ввел не правильный номер пункта из меню. "
                "Пользователь ввел: %s. Нужно ввести цифру от %s до %s. ",
                user_input,
                min(menu),
                max(menu),
            )
            print(f"Вы должны ввести цифру (от {min(menu)} до {max(menu)})")
            continue

        choice = int(user_input)
        logger.info("Пользователь выбрал пункт меню: %s (%s)", choice, menu[choice])
        return choice

    raise RuntimeError("for mypy")


def run_interface(db_manager: DBManager) -> None:
    """
    Запускает основной цикл пользовательского интерфейса программы.

    Функция отображает меню, обрабатывает ввод пользователя, выполняет
    соответствующие действия (вывод вакансий, поиск, фильтрация) и
    обеспечивает корректное завершение работы при выборе пункта «Выход».

    :param db_manager: Объект класса DBManager
    """

    while True:

        user_input = show_menu()

        if user_input == 1:
            handle_show_companies(db_manager)

        elif user_input == 2:
            handle_show_vacancies(
                data=db_manager.get_all_vacancies(),
                method_name="get_all_vacancies",
                menu_title="показать все вакансии",
            )

        elif user_input == 3:
            handle_show_avg_salary(db_manager)

        elif user_input == 4:
            handle_show_vacancies(
                data=db_manager.get_vacancies_with_higher_salary(),
                method_name="get_vacancies_with_higher_salary",
                menu_title="показать вакансии с зарплатой выше средней",
            )

        elif user_input == 5:
            keyword = input("Введите ключевое слово для поиска вакансии -----> ")
            handle_show_vacancies(
                data=db_manager.get_vacancies_with_keyword(keyword),
                method_name=f"get_vacancies_with_keyword('{keyword}')",
                menu_title=f"поиск вакансий по ключевому слову: {keyword}",
            )

        elif user_input == 6:
            logger.info("Выполняется пункт меню: выход из программы")
            print("Выход из программы...")
            break


def _checking_list_data(data: list, method_name: str, empty_message: str) -> bool:
    """
    Функция проверяет, что список с данными.
    Проверка:
       - что список это список.
       - что все элементы списка словари.
       - что список не пусто.

    :param data: Список с данными
    :param method_name: Название метода
    :param empty_message: Сообщение для пользователя, если список пустой
    :return: True/False
    """

    if not isinstance(data, list):
        logger.error("%s должен вернуть list[dict], а получено: %s", method_name, type(data).__name__)
        print("Произошла внутренняя ошибка. Обратитесь к разработчику.")
        return False

    if not all(isinstance(d, dict) for d in data):
        logger.error("%s должен вернуть list, где каждый элемент dict", method_name)
        print("Произошла внутренняя ошибка. Обратитесь к разработчику.")
        return False

    if not data:
        logger.warning("%s вернул пустой список", method_name)
        print(empty_message)
        return False

    return True


def handle_show_companies(db_manager: DBManager) -> None:
    """
    Обработчик пункта меню: показать компании и количество вакансий.
    :param db_manager: Объект класса DBManager
    """

    logger.info("Выполняется пункт меню: показать компании и количество вакансий")
    result = db_manager.get_companies_and_vacancies_count()

    if not _checking_list_data(
        result,
        "get_companies_and_vacancies_count",
        "Данные о компаниях отсутствуют.",
    ):
        return None

    logger.info("Получено %s компаний", len(result))

    for d in result:
        print(f"Название компания: {d['name']}, количество вакансии: {d['vacancy_count']}")


def handle_show_vacancies(*, data: list[dict], method_name: str, menu_title: str) -> None:
    """
    Обработчик пункта меню: показать все вакансии и показать вакансии с зарплатой выше средней.
    :param data: Список с вакансиями
    :param method_name: Название метод для запроса к sql
    :param menu_title: Описание метода
    """

    logger.info("Выполняется пункт меню: %s", menu_title)

    if not _checking_list_data(data, method_name, "Данные о вакансиях отсутствуют."):
        return None

    logger.info("Получено %s вакансии", len(data))

    for d in data:
        name = d["name"]
        title = d["title"]
        salary_from = d["salary_from"]
        salary_to = d["salary_to"]
        url = d["url"]

        if salary_from and salary_to:
            salary_msg = f"от {salary_from} до {salary_to}"
        elif salary_from:
            salary_msg = f"от {salary_from}"
        elif salary_to:
            salary_msg = f"до {salary_to}"
        else:
            salary_msg = "Данных нет"

        print(f"[{name}] {title}\n" f"Заработная плата: {salary_msg}\n" f"Ссылка: {url}\n" f"{'-' * 44}")


def handle_show_avg_salary(db_manager: DBManager) -> None:
    """
    Обработчик пункта меню: показать среднею зарплату по всем вакансиям.
    :param db_manager: Объект класса DBManager
    """

    logger.info("Выполняется пункт меню: среднею зарплату по всем вакансиям")
    result = db_manager.get_avg_salary()

    if result is None:
        print("Данные о заработной плате отсутствуют, поэтому расчет средней заработной платы не возможен.")
    else:
        print(f"Средняя заработная плата по всем вакансиям: {result}")
