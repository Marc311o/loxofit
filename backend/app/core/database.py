from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.core.config import settings


class Base(DeclarativeBase):
    metadata = MetaData()


engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=settings.SQL_ECHO)

SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[Session]:
    with SessionLocal() as db:
        yield db


SessionDep = Annotated[AsyncSession, Depends(get_db)]
