from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.modules.auth.models import User


def authenticate(db: Session, username: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.username == username))
    if user and user.active and verify_password(password, user.password_hash):
        return user
    return None
