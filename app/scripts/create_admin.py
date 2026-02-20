"""
Create an admin user. Run once to bootstrap the first admin.
Usage: python -m app.scripts.create_admin
"""
import asyncio
import getpass
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import select
from app.database import init_db
from app.models import User, UserRole
from app.auth import hash_password


async def main():
    from app.database import get_session_factory

    await init_db()
    session_factory = get_session_factory()
    async with session_factory() as db:
        username = input("Admin username: ").strip()
        if not username:
            print("Username required.")
            return
        existing = await db.execute(select(User).where(User.username == username))
        if existing.scalar_one_or_none():
            print("User already exists. Use a different username or reset password in DB.")
            return
        password = getpass.getpass("Password: ")
        if len(password) < 6:
            print("Password must be at least 6 characters.")
            return
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=UserRole.admin,
        )
        db.add(user)
        await db.commit()
        print("Admin user created:", username)


if __name__ == "__main__":
    asyncio.run(main())
