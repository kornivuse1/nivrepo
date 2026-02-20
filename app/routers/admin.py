from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_admin
from app.models import User, Song, BackgroundImage, SongLove
from app.services.song_service import (
    list_songs,
    get_song_by_id,
    create_song_from_upload,
    delete_song as delete_song_service,
    safe_extension,
)
from app.config import get_settings

router = APIRouter(prefix="/api/admin/songs", tags=["admin"])


class SongOut(BaseModel):
    id: int
    title: str
    artist: str
    duration_seconds: float | None
    filename: str
    love_count: int = 0

    @classmethod
    def from_orm_song(cls, s: Song, love_count: int = 0) -> "SongOut":
        return cls(
            id=s.id,
            title=s.title,
            artist=s.artist,
            duration_seconds=s.duration_seconds,
            filename=s.filename,
            love_count=love_count,
        )


@router.get("", response_model=list[SongOut])
async def admin_list_songs(
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    songs = await list_songs(db, search=search)
    result = []
    for song in songs:
        love_count_result = await db.execute(
            select(func.count(SongLove.id)).where(SongLove.song_id == song.id)
        )
        love_count = love_count_result.scalar() or 0
        result.append(SongOut.from_orm_song(song, love_count=love_count))
    return result


@router.post("", response_model=SongOut)
async def upload_song(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    if not file.filename or not safe_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid or missing file. Allowed: mp3, m4a, ogg, wav, flac",
        )
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        song = await create_song_from_upload(db, file.filename, content)
        return SongOut.from_orm_song(song)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class SongUpdate(BaseModel):
    title: str | None = None
    artist: str | None = None


@router.patch("/{song_id}", response_model=SongOut)
async def update_song(
    song_id: int,
    update_data: SongUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    song = await get_song_by_id(db, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    if update_data.title is not None:
        song.title = update_data.title.strip() if update_data.title.strip() else song.title
    if update_data.artist is not None:
        song.artist = update_data.artist.strip() if update_data.artist.strip() else song.artist
    await db.commit()
    await db.refresh(song)
    return SongOut.from_orm_song(song)


@router.delete("/{song_id}")
async def delete_song(
    song_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    song = await get_song_by_id(db, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    await delete_song_service(db, song)
    return {"ok": True}
