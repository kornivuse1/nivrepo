from datetime import datetime
from pathlib import Path
from sqlalchemy import String, Integer, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)  # stored filename on disk
    title: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    artist: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def path_for(self, upload_root: Path) -> Path:
        return upload_root / self.filename
