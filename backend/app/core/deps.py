"""Shared request dependencies: who is calling, and are they allowed."""

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import DomainError
from app.core.security import decode_access_token
from app.modules.audit import service as audit
from app.modules.auth.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    payload = decode_access_token(token) if token else None
    user = db.get(User, int(payload["sub"])) if payload else None
    if not user or not user.active:
        raise DomainError(401, "not_authenticated", "Please log in")
    return user


def require_roles(*roles: str):
    def checker(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        if user.role not in roles:
            audit.record(
                db,
                actor=user,
                action="access.denied",
                entity_type="endpoint",
                detail={"allowed_roles": list(roles)},
                outcome="denied",
            )
            db.commit()
            raise DomainError(403, "forbidden", f"Role '{user.role}' is not allowed to do this")
        return user

    return checker
