"""Postgres connections."""

import psycopg

from python_template import config

__all__ = ["open_connection"]


def open_connection() -> psycopg.Connection:
    """Open a connection to the database in `config.settings`.

    Use it as a context manager: the block commits, and leaving it closes the connection.
    """
    connection = psycopg.connect(config.settings.database_url)

    return connection
