import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import SessionDep, engine
from app.core.errors import ErrorResponse, ServiceUnavailableError, register_exception_handlers
from app.domains.auth.router import router as auth_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_STR}/docs",
    lifespan=lifespan,
)

register_exception_handlers(app)
api_router = APIRouter(prefix=settings.API_V1_STR)


@api_router.get(path="/health", tags=["health"], responses={503: {"model": ErrorResponse}})
async def health(db: SessionDep) -> dict[str, str]:
    try:
        await db.execute(text("SELECT 1"))
    except SQLAlchemyError as e:
        raise ServiceUnavailableError("No established connection to database") from e
    return {"status": "ok"}


api_router.include_router(auth_router)
app.include_router(api_router)
