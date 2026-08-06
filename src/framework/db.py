from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL

from framework.config import Settings


def engine(settings: Settings) -> Engine:
    url = URL.create(
        drivername="mysql+pymysql",
        username=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
    )
    return create_engine(url, isolation_level="AUTOCOMMIT")
