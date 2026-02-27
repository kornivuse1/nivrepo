from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.config import get_settings
from app.database import get_db
from app.auth import get_current_admin
from app.models import AppSettings

router = APIRouter(prefix="/api/admin/settings", tags=["admin"])


class SettingsOut(BaseModel):
    auto_change_background: bool
    allow_registration: bool


@router.get("", response_model=SettingsOut)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_admin),
):
    result = await db.execute(select(AppSettings).limit(1))
    settings = result.scalar_one_or_none()
    if not settings:
        config = get_settings()
        settings = AppSettings(
            auto_change_background=False,
            allow_registration=config.allow_registration,
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return SettingsOut(
        auto_change_background=settings.auto_change_background,
        allow_registration=getattr(settings, "allow_registration", get_settings().allow_registration),
    )


class SettingsUpdate(BaseModel):
    auto_change_background: bool | None = None
    allow_registration: bool | None = None


@router.patch("", response_model=SettingsOut)
async def update_settings(
    update_data: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_admin),
):
    result = await db.execute(select(AppSettings).limit(1))
    settings = result.scalar_one_or_none()
    if not settings:
        config = get_settings()
        settings = AppSettings(
            auto_change_background=False,
            allow_registration=config.allow_registration,
        )
        db.add(settings)
    if update_data.auto_change_background is not None:
        settings.auto_change_background = update_data.auto_change_background
    if update_data.allow_registration is not None:
        settings.allow_registration = update_data.allow_registration
    await db.commit()
    await db.refresh(settings)
    return SettingsOut(
        auto_change_background=settings.auto_change_background,
        allow_registration=getattr(settings, "allow_registration", False),
    )
