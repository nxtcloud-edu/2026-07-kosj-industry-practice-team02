from psycopg_pool import AsyncConnectionPool


def create_pool(database_url: str) -> AsyncConnectionPool:
    if not database_url.strip():
        raise ValueError("DATABASE_URL_REQUIRED")
    return AsyncConnectionPool(
        conninfo=database_url,
        min_size=1,
        max_size=4,
        open=False,
        kwargs={"autocommit": False},
    )
