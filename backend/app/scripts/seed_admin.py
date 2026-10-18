import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.domains.users.enums import UserRole
from app.domains.users.service import UserService

logger = logging.getLogger("seed")


async def seed_admin(db: AsyncSession) -> None:
    email, password = settings.FIRST_SUPERUSER_EMAIL, settings.FIRST_SUPERUSER_PASSWORD
    if not email or not password:
        logger.info("No FIRST_SUPERUSER_EMAIL/PASSWORD in .env – skipping")
        return

    users = UserService(db)
    if await users.get_by_email(email) is not None:
        logger.info(f"Admin {email} already exists - skipping")
        return

    await users.create(email=email, password=password, display_name="Admin", role=UserRole.ADMIN)
    await db.commit()
    logger.info(f"{email} administrator created")


async def main() -> None:
    try:
        async with SessionLocal() as db:
            await seed_admin(db)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    asyncio.run(main())
