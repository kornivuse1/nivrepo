from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_viewer
from app.models import User, Song, BackgroundImage, SongLove
from app.services.song_service import list_songs, get_song_by_id
from app.config import get_settings
from sqlalchemy import func

router = APIRouter(prefix="/api/songs", tags=["player"])


class SongOut(BaseModel):
    id: int
    title: str
    artist: str
    duration_seconds: float | None
    filename: str
    love_count: int = 0
    is_loved: bool = False

    @classmethod
    def from_orm_song(cls, s: Song, love_count: int = 0, is_loved: bool = False) -> "SongOut":
        return cls(
            id=s.id,
            title=s.title,
            artist=s.artist,
            duration_seconds=s.duration_seconds,
            filename=s.filename,
            love_count=love_count,
            is_loved=is_loved,
        )


@router.get("", response_model=list[SongOut])
async def list_songs_api(
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_viewer),
):
    songs = await list_songs(db, search=search)
    result = []
    for song in songs:
        # Get love count
        love_count_result = await db.execute(
            select(func.count(SongLove.id)).where(SongLove.song_id == song.id)
        )
        love_count = love_count_result.scalar() or 0
        # Check if current user loved it
        user_love_result = await db.execute(
            select(SongLove).where(SongLove.song_id == song.id, SongLove.user_id == user.id).limit(1)
        )
        is_loved = user_love_result.scalar_one_or_none() is not None
        result.append(SongOut.from_orm_song(song, love_count=love_count, is_loved=is_loved))
    return result


@router.get("/{song_id}/stream")
async def stream_song(
    song_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_viewer),
):
    song = await get_song_by_id(db, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    settings = get_settings()
    path = song.path_for(settings.upload_dir)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path,
        media_type="audio/mpeg",
        filename=song.title or song.filename,
    )


@router.get("/background/active")
async def get_active_background(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_viewer),
):
    """Get the active background image (public for authenticated users)"""
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


@router.get("/background/random")
async def get_random_background(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_viewer),
):
    """Get a random background image (for auto-change feature)"""
    import random
    result = await db.execute(select(BackgroundImage))
    images = list(result.scalars().all())
    if not images:
        raise HTTPException(status_code=404, detail="No backgrounds available")
    img = random.choice(images)
    settings = get_settings()
    settings.images_dir.mkdir(parents=True, exist_ok=True)
    path = img.path_for(settings.images_dir)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="image/jpeg")


@router.get("/settings/auto-change-bg")
async def get_auto_change_setting(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_viewer),
):
    """Get auto-change background setting (for players)"""
    from app.models import AppSettings
    result = await db.execute(select(AppSettings).limit(1))
    settings = result.scalar_one_or_none()
    return {"auto_change_background": settings.auto_change_background if settings else False}


@router.post("/{song_id}/love")
async def love_song(
    song_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_viewer),
):
    """Love a song"""
    song = await get_song_by_id(db, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    # Check if already loved
    existing = await db.execute(
        select(SongLove).where(SongLove.song_id == song_id, SongLove.user_id == user.id).limit(1)
    )
    if existing.scalar_one_or_none():
        return {"loved": True, "message": "Already loved"}
    love = SongLove(user_id=user.id, song_id=song_id)
    db.add(love)
    await db.commit()
    return {"loved": True}


@router.delete("/{song_id}/love")
async def unlove_song(
    song_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_viewer),
):
    """Unlove a song"""
    result = await db.execute(
        select(SongLove).where(SongLove.song_id == song_id, SongLove.user_id == user.id).limit(1)
    )
    love = result.scalar_one_or_none()
    if not love:
        return {"loved": False, "message": "Not loved"}
    await db.delete(love)
    await db.commit()
    return {"loved": False}
