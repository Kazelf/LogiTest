from collections.abc import Iterator

import psycopg

from app.core.settings import settings


def get_database_url() -> str:
    return settings.database_url


def connect() -> psycopg.Connection:
    return psycopg.connect(get_database_url())


def get_connection() -> Iterator[psycopg.Connection]:
    with connect() as conn:
        yield conn
