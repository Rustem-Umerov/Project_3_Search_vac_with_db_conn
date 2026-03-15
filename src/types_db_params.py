from typing import TypedDict


class DbParams(TypedDict):
    """Строго типизированный словарь с параметрами подключения к PostgreSQL."""

    dbname: str
    user: str
    password: str
    host: str
    port: int
