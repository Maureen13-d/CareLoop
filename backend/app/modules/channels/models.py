from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class UssdSession(Base):
    __tablename__ = "ussd_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    phone_ref: Mapped[str] = mapped_column(String(20))
    menu: Mapped[str] = mapped_column(String(20), default="home")
    scratch: Mapped[str | None] = mapped_column(String(200), nullable=True)
    updated_at: Mapped[datetime]


class SmsMessage(Base):
    __tablename__ = "sms_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone_ref: Mapped[str] = mapped_column(String(20), index=True)
    direction: Mapped[str] = mapped_column(String(3))  # in | out
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime]


class SmsOptOut(Base):
    __tablename__ = "sms_opt_outs"

    phone_ref: Mapped[str] = mapped_column(String(20), primary_key=True)
    opted_out_at: Mapped[datetime]
