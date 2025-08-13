from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'user'

    id: Mapped[str] = mapped_column(
        String, primary_key=True, nullable=False)
    user_name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    pwd_hash: Mapped[str] = mapped_column(Text, nullable=False)

    todos: Mapped[List[Todo]] = relationship(
        back_populates='owner_user',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<User(id={self.id!r}, user_name={self.user_name!r})>'


class Todo(Base):
    __tablename__ = 'todo'

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement='auto')
    todo: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(
        default=lambda: datetime.now(timezone.utc).isoformat())
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    owner: Mapped[str] = mapped_column(ForeignKey('user.id'))

    owner_user: Mapped[User] = relationship(back_populates='todos')

    def __repr__(self) -> str:
        return f'<Todo(id={self.id}, todo={self.todo!r}, done={self.done})>'
