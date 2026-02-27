import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserRole(str, enum.Enum):
    viewer = "viewer"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.viewer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    last_login_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    def is_admin(self) -> bool:
        return self.role == UserRole.admin
