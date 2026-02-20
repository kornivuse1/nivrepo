from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_admin
from app.models import BackgroundImage
from app.config import get_settings

router = APIRouter(prefix="/api/admin/backgrounds", tags=["admin"])

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def safe_image_extension(filename: str) -> str | None:
    ext = Path(filename).suffix.lower()
    return ext if ext in ALLOWED_IMAGE_EXTENSIONS else None


class BackgroundImageOut(BaseModel):
    id: int
    filename: str
    is_active: bool

    @classmethod
    def from_orm(cls, img: BackgroundImage) -> "BackgroundImageOut":
        return cls(id=img.id, filename=img.filename, is_active=img.is_active)


@router.get("", response_model=list[BackgroundImageOut])
async def list_backgrounds(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_admin),
):
    result = await db.execute(select(BackgroundImage).order_by(BackgroundImage.created_at.desc()))
    images = list(result.scalars().all())
    return [BackgroundImageOut.from_orm(img) for img in images]


@router.get("/active")
async def get_active_background(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BackgroundImage).where(BackgroundImage.is_active == True).limit(1))
    img = result.scalar_one_or_none()
    if not img:
        raise HTTPException(status_code=404, detail="No active background")
    settings = get_settings()
    settings.images_dir.mkdir(parents=True, exist_ok=True)
    path = img.path_for(settings.images_dir)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="image/jpeg")


@router.post("", response_model=BackgroundImageOut)
async def upload_background(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_admin),
):
    if not file.filename or not safe_image_extension(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file. Allowed: jpg, jpeg, png, gif, webp")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    settings = get_settings()
    settings.images_dir.mkdir(parents=True, exist_ok=True)
    ext = safe_image_extension(file.filename)
    stored_name = f"{uuid4().hex}{ext}"
    dest = settings.images_dir / stored_name
    dest.write_bytes(content)
    img = BackgroundImage(filename=stored_name, is_active=False)
    db.add(img)
    await db.commit()
    await db.refresh(img)
    return BackgroundImageOut.from_orm(img)


@router.post("/{image_id}/activate")
async def activate_background(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_admin),
):
    result = await db.execute(select(BackgroundImage).where(BackgroundImage.id == image_id))
    img = result.scalar_one_or_none()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    # Deactivate all
    await db.execute(update(BackgroundImage).where(BackgroundImage.is_active == True).values(is_active=False))
    # Activate this one
    img.is_active = True
    await db.commit()
    return {"ok": True}


@router.delete("/{image_id}")
async def delete_background(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_admin),
):
    result = await db.execute(select(BackgroundImage).where(BackgroundImage.id == image_id))
    img = result.scalar_one_or_none()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    settings = get_settings()
    path = img.path_for(settings.images_dir)
    if path.exists():
        path.unlink(missing_ok=True)
    await db.delete(img)
    await db.commit()
    return {"ok": True}
