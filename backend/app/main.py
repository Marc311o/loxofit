import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import SessionDep, SessionLocal, engine
from app.core.errors import ErrorResponse, ServiceUnavailableError, register_exception_handlers
from app.domains.auth.router import router as auth_router
from app.domains.catalog.router import router as catalog_router
from app.domains.generator.repository import GenerationRepository
from app.domains.generator.router import router as generator_router
from app.domains.generator.runner import GenerationRunner
from app.domains.plans.router import router as plans_router
from app.domains.users.router import router as users_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TODO: add 2FA to auth domain
# TODO: reset password


async def _fail_interrupted_generations() -> None:
    """Generations that were running when the server stopped will never finish."""
    try:
        async with SessionLocal() as db:
            if count := await GenerationRepository(db).fail_interrupted():
                logger.warning("Marked %d interrupted generation(s) as failed", count)
            await db.commit()
    except SQLAlchemyError:
        logger.exception("Could not mark interrupted generations - is the database up?")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await _fail_interrupted_generations()
    app.state.generator = GenerationRunner.in_processes(settings.GENERATOR_WORKERS, SessionLocal)
    yield
    app.state.generator.close()
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
api_router.include_router(catalog_router)
api_router.include_router(generator_router)
api_router.include_router(plans_router)
api_router.include_router(users_router)
app.include_router(api_router)
