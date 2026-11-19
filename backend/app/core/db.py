"""Database engine and session handling (SQLite by default)."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def make_engine(url: str, **kwargs):
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, **kwargs)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def import_models() -> None:
    """Import every module's models so their tables are registered on Base."""
    from app.modules.audit import models as _a  # noqa: F401
    from app.modules.auth import models as _b  # noqa: F401
    from app.modules.channels import models as _f  # noqa: F401
    from app.modules.interop import models as _h  # noqa: F401
    from app.modules.pathways import models as _d  # noqa: F401
    from app.modules.patients import models as _c  # noqa: F401
    from app.modules.screenings import models as _e  # noqa: F401
    from app.modules.tasks import models as _g  # noqa: F401


def init_db(bind=None) -> None:
    import_models()
    Base.metadata.create_all(bind or engine)
