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
            paginate_vacancies(
                data=db_manager.get_all_vacancies(),
                method_name="get_all_vacancies",
                menu_title="показать все вакансии",
            )

        elif user_input == 3:
            handle_show_avg_salary(db_manager)

        elif user_input == 4:
            paginate_vacancies(
                data=db_manager.get_vacancies_with_higher_salary(),
                method_name="get_vacancies_with_higher_salary",
                menu_title="показать вакансии с зарплатой выше средней",
            )

        elif user_input == 5:
            keyword_query(db_manager)

        elif user_input == 6:
            logger.info("Выполняется пункт меню: выход из программы")
            print("Выход из программы...")
            break


def keyword_query(db_manager: DBManager) -> None:
    """
    Запрашивает у пользователя ключевое слово для поиска вакансии.
    Если пользователь отправил пустой ввод, то цикл продолжается пока пользователь не введет хотя бы один символ.

    :param db_manager: Объект класса DBManager
    """

    while True:
        keyword = input("Введите ключевое слово для поиска вакансии -----> ")
        if not keyword.strip():
            print("Пустой запрос. Введите хотя бы один символ.")
            continue

        logger.info("Пользователь ищет вакансии по ключевому слову: %s", keyword)
        paginate_vacancies(
            data=db_manager.get_vacancies_with_keyword(keyword),
            method_name=f"get_vacancies_with_keyword('{keyword}')",
            menu_title=f"поиск вакансий по ключевому слову: {keyword}",
        )
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

    logger.debug("%s: данные прошли проверку", method_name)
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
        logger.debug("Компания: %s, количество вакансий: %s", d["name"], d["vacancy_count"])

        name_company_str = f"Название компания: {d['name']}"
        left = name_company_str.ljust(90)
        right = f"| Количество вакансии: {d['vacancy_count']}"
        print(left + right)
        print("-" * 150)


def paginate_vacancies(*, data: list[dict], method_name: str, menu_title: str) -> None:
    """
    Постраничный вывод вакансий.

    :param data: Список с вакансиями
    :param method_name: Название метода
    :param menu_title: Описание метода
    """

    logger.info("Выполняется пункт меню: %s", menu_title)

    if not _checking_list_data(data, method_name, "Данные о вакансиях отсутствуют."):
        logger.warning("Пагинация прервана: список вакансий пуст.")
        return None

    total = len(data)
    logger.info("Получено %s вакансии", total)

    page_size = 20
    start = 0

    # вычисляем количество страниц
    total_pages = (total - 1) // page_size + 1

    logger.debug(
        "Инициализация пагинации: page_size=%s, total_pages=%s",
        page_size,
        total_pages,
    )

    while True:
        current_page = start // page_size + 1
        start_index = start + 1
        end_index = min(start + page_size, total)

        logger.debug(
            "Отображение страницы %s/%s (вакансии %s–%s)",
            current_page,
            total_pages,
            start_index,
            end_index,
        )

        print()
        print(f"Всего вакансий: {total}")
        print(f"Страница {current_page} из {total_pages}")
        print(f"Вакансии: {start_index}–{end_index}")
        print()

        # текущая страница
        page = data[start : start + page_size]
        handle_show_vacancies(page)

        new_start = next_or_prev_page(start=start, page_size=page_size, total=total)

        if new_start is None:
            logger.info("Пользователь вышел из пагинации")
            return None

        start = new_start


def next_or_prev_page(*, start: int, page_size: int, total: int) -> Optional[int]:
    """
    Обрабатывает выбор пользователя: следующая/предыдущая/выход.

    :param start: Начальный индекс
    :param page_size: Размер страницы
    :param total: Общее количество вакансии
    :return:
    """

    while True:
        menu = {
            1: "Перейти на следующую страницу",
            2: "Перейти на предыдущую страницу",
            3: "Выйти в главное меню",
        }

        print()
        for key, value in menu.items():
            print(f"{key}: {value}")
        print()

        choice = validating_user_input(menu=menu)
        logger.debug("Пользователь выбрал пункт меню: %s", choice)

        # Следующая страница
        if choice == 1:
            if start + page_size < total:
                new_start = start + page_size
                logger.debug("Переход на следующую страницу: start=%s", new_start)
                return new_start
            else:
                print("-" * 50)
                print(f"!!!{' ' * 10}Вы на последней странице")
                print("-" * 50)
                logger.info("Попытка перейти на страницу дальше, будучи на последней странице")
                continue

        # Предыдущая страница
        elif choice == 2:
            if start > 0:
                new_start = start - page_size
                logger.debug("Переход на предыдущую страницу: start=%s", new_start)
                return new_start
            else:
                print("-" * 50)
                print(f"!!!{' ' * 10}Вы на первой странице")
                print("-" * 50)
                logger.info("Попытка перейти на страницу назад, будучи на первой страницей")
                continue

        # Выход
        elif choice == 3:
            logger.info("Выход в главное меню из пагинации")
            return None


def handle_show_vacancies(data: list[dict]) -> None:
    """
    Обработчик пункта меню: показать все вакансии и показать вакансии с зарплатой выше средней.
    :param data: Список с вакансиями
    """

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

        print((f"[{name}] {title}\n" f"Заработная плата: {salary_msg}\n" f"Ссылка: {url}\n" f"{'-' * 44}"))


def handle_show_avg_salary(db_manager: DBManager) -> None:
    """
    Обработчик пункта меню: показать среднею зарплату по всем вакансиям.
    :param db_manager: Объект класса DBManager
    """

    logger.info("Выполняется пункт меню: среднею зарплату по всем вакансиям")
    result = db_manager.get_avg_salary()

    if result is None:
        logger.warning("Данные о заработной плате отсутствуют, поэтому расчет средней заработной платы не возможен.")
        print("Данные о заработной плате отсутствуют, поэтому расчет средней заработной платы не возможен.")
    else:
        logger.info("Средняя заработная плата по всем вакансиям: %s", result)
        print(f"Средняя заработная плата по всем вакансиям: {result}")
