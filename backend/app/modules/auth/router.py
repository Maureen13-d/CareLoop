from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.errors import DomainError
from app.core.security import create_access_token
from app.modules.audit import service as audit
from app.modules.auth import service
from app.modules.auth.schemas import TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = service.authenticate(db, form.username, form.password)
    if not user:
        audit.record(db, actor=None, action="auth.login", entity_type="user", detail={"username": form.username}, outcome="denied")
        db.commit()
        raise DomainError(401, "invalid_credentials", "Incorrect username or password")
    audit.record(db, actor=user, action="auth.login", entity_type="user", entity_id=user.id)
    db.commit()
    return TokenOut(access_token=create_access_token(user.id, user.role))


@router.get("/me", response_model=UserOut)
def me(user=Depends(get_current_user)):
    return user
