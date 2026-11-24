"""
Sets a new password for a user who forgot theirs - until reset by e-mail exists.

    python -m app.admin.reset_password anna@example.com

Prints a random temporary password to pass on to the user, who then changes it in the
profile. Every session of the user ends.
"""

import argparse
import asyncio
import secrets
import sys
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal, engine
from app.domains.auth.repository import RefreshTokenRepository
from app.domains.users.service import UserService


def temporary_password() -> str:
    return secrets.token_urlsafe(12)  # 16 characters


async def reset_password(db: AsyncSession, email: str, password: str) -> bool:
    """False when there is no such user."""
    users = UserService(db)
    user = await users.get_by_email(email)
    if user is None:
        return False
    users.set_password(user, password)
    await RefreshTokenRepository(db).revoke_all_for_user(user.id, datetime.now(UTC))
    await db.commit()
    return True


async def main(email: str) -> int:
    password = temporary_password()
    try:
        async with SessionLocal() as db:
            if not await reset_password(db, email, password):
                print(f"No user with e-mail {email}", file=sys.stderr)
                return 1
    finally:
        await engine.dispose()
    print(f"New password for {email}: {password}")
    print("Pass it on to the user - they should change it in the profile.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("email")
    sys.exit(asyncio.run(main(parser.parse_args().email)))
