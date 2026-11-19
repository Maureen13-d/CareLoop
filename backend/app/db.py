from collections.abc import Iterator

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app import tables  # noqa: F401  (importing registers the tables on SQLModel.metadata)
from app.config import settings


def make_engine(url: str) -> Engine:
    kwargs: dict = {"connect_args": {"check_same_thread": False}}  # FastAPI uses a threadpool
    if url in {"sqlite://", "sqlite:///:memory:"}:
        kwargs["poolclass"] = StaticPool  # one shared connection, so the in-memory DB persists

    eng = create_engine(url, **kwargs)

    @event.listens_for(eng, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):  # SQLite ignores FKs unless asked
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return eng


engine = make_engine(settings.database_url)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
