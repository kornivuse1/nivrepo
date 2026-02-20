from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Song

# Allowed extensions for upload
ALLOWED_EXTENSIONS = {".mp3", ".m4a", ".ogg", ".wav", ".flac"}


def safe_extension(filename: str) -> str | None:
    ext = Path(filename).suffix.lower()
    return ext if ext in ALLOWED_EXTENSIONS else None


def parse_tags(file_path: Path) -> tuple[str, str, float | None]:
    """Try to get title, artist, duration from file tags. Fallback to filename."""
    title = ""
    artist = ""
    duration: float | None = None
    try:
        from mutagen import File as MutagenFile
        f = MutagenFile(file_path)
        if f is not None:
            if "title" in f:
                title = str(f["title"][0]).strip() or ""
            if "artist" in f:
                artist = str(f["artist"][0]).strip() or ""
            if f.info and hasattr(f.info, "length"):
                duration = float(f.info.length)
    except Exception:
        pass
    stem = file_path.stem
    if not title:
        title = stem
    if not artist:
        artist = "Unknown"
    return title, artist, duration


async def create_song_from_upload(
    db: AsyncSession,
    original_filename: str,
    file_content: bytes,
) -> Song:
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    ext = safe_extension(original_filename)
    if not ext:
        raise ValueError(f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    stored_name = f"{uuid4().hex}{ext}"
    dest = settings.upload_dir / stored_name
    dest.write_bytes(file_content)
    title, artist, duration = parse_tags(dest)
    song = Song(filename=stored_name, title=title, artist=artist, duration_seconds=duration)
    db.add(song)
    await db.flush()
    await db.refresh(song)
    return song


async def get_song_by_id(db: AsyncSession, song_id: int) -> Song | None:
    result = await db.execute(select(Song).where(Song.id == song_id))
    return result.scalar_one_or_none()


async def list_songs(db: AsyncSession, search: str | None = None) -> list[Song]:
    q = select(Song).order_by(Song.created_at.desc())
    if search and search.strip():
        term = f"%{search.strip()}%"
        q = q.where(Song.title.ilike(term) | Song.artist.ilike(term) | Song.filename.ilike(term))
    result = await db.execute(q)
    return list(result.scalars().all())


async def delete_song(db: AsyncSession, song: Song) -> None:
    settings = get_settings()
    path = song.path_for(settings.upload_dir)
    if path.exists():
        path.unlink(missing_ok=True)
    await db.delete(song)
