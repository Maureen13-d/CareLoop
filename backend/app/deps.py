from fastapi import Depends
from sqlmodel import Session

from app.db import get_session
from app.repository import Repository


def get_repo(session: Session = Depends(get_session)) -> Repository:
    return Repository(session)
