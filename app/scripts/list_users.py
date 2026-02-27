"""
List all users (admins and viewers).
Usage: python -m app.scripts.list_users
"""
import asyncio
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import select
from app.database import init_db
from app.models import User


async def main():
    from app.database import get_session_factory

    await init_db()
    session_factory = get_session_factory()
    async with session_factory() as db:
        result = await db.execute(select(User).order_by(User.id))
        users = list(result.scalars().all())
        if not users:
            print("No users yet.")
            return
        # Header
        print(f"{'id':<5} {'username':<20} {'role':<8} {'created_at':<22} {'last_ip'}")
        print("-" * 75)
        for u in users:
            created = u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else ""
            ip = getattr(u, "last_login_ip", None) or getattr(u, "created_ip", None) or ""
            print(f"{u.id:<5} {u.username:<20} {u.role.value:<8} {created:<22} {ip}")


if __name__ == "__main__":
    asyncio.run(main())
