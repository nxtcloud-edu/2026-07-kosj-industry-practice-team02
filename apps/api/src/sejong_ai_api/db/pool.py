import os
from collections.abc import Mapping

from psycopg_pool import AsyncConnectionPool

_LOCAL_DATABASE_HOSTADDR = "127.0.0.1"


def _ambient_libpq_environment_is_clear(environment: Mapping[str, str]) -> bool:
    return not any(
        name.upper().startswith("PG") and value != "" for name, value in environment.items()
    )


def create_pool(database_url: str) -> AsyncConnectionPool:
    if not _ambient_libpq_environment_is_clear(os.environ):
        raise ValueError("AMBIENT_LIBPQ_ENVIRONMENT_INVALID")
    if not database_url.strip():
        raise ValueError("DATABASE_URL_REQUIRED")
    return AsyncConnectionPool(
        conninfo=database_url,
        min_size=1,
        max_size=4,
        open=False,
        kwargs={"autocommit": False, "hostaddr": _LOCAL_DATABASE_HOSTADDR},
    )
