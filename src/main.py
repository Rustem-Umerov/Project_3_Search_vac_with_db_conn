from src.config import settings
from src.db_creator import connect_to_db, init_database, load_data
from src.db_manager import DBManager
from src.logger_setup import get_logger
from src.user_interface import run_interface

logger = get_logger(__name__)


def main() -> None:
    """
    Точка входа в приложение.
    Полная инициализация базы, проверка данных, запуск интерфейса.
    """

    # 1. Инициализация базы (создание БД и таблиц при необходимости)
    init_database()

    # 2. Подключение для проверки содержимого таблиц
    conn = connect_to_db(settings.DB_NAME)

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM companies")
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("Не удалось получить количество компаний")
        companies_count = row[0]

        cur.execute("SELECT COUNT(*) FROM vacancies")
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("Не удалось получить количество вакансий")
        vacancies_count = row[0]

    # 3. Логика проверки данных
    if companies_count == 0 and vacancies_count == 0:
        logger.info("Таблицы пустые — начинаем загрузку данных")
        load_data(conn)

    elif companies_count > 0 and vacancies_count > 0:
        logger.info("Данные уже присутствуют в таблицах")

    else:
        logger.error(
            "Неконсистентное состояние БД: companies=%s, vacancies=%s",
            companies_count,
            vacancies_count,
        )
        conn.close()
        raise RuntimeError("Неконсистентные данные в таблицах")

    # 4. Закрываем соединение, использованное для загрузки/проверки
    conn.close()

    # 5. Создаём менеджер БД (он откроет своё собственное соединение)
    db_manager = DBManager()

    # 6. Запускаем интерфейс
    run_interface(db_manager)

    # 7. Закрываем соединение менеджера
    db_manager.close()

    logger.info("Программа завершена")


if __name__ == "__main__":
    main()
