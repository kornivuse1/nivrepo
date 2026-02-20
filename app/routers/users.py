from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_admin
from app.models import User

router = APIRouter(prefix="/api/admin/users", tags=["admin"])


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    created_at: str

    @classmethod
    def from_orm(cls, u: User) -> "UserOut":
        return cls(
            id=u.id,
            username=u.username,
            role=u.role.value,
            created_at=u.created_at.isoformat() if u.created_at else "",
        )


@router.get("", response_model=list[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = list(result.scalars().all())
    return [UserOut.from_orm(u) for u in users]


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    if user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(target_user)
    await db.commit()
    return {"ok": True}
